"""firm.mltrain -- training infrastructure at laptop scale (Book 12, chapter 23).

Tick data stored as per-session shards in three formats (CSV text, NumPy files, one memory-mapped float32 file with a
JSON index), a sampler of training windows that never crosses a session boundary and whose state can be saved, a
trainer with gradient accumulation and bfloat16 autocast on the CPU, a data-parallel step simulated in one process
(per-shard gradients averaged, which is what an all-reduce computes), and checkpoints holding everything needed to
resume a run bitwise: model, optimiser, sampler and generator states and the step count. One thread, no worker
processes.

API (stable):
    write_shards(sessions, root, fmt) -> None             fmt 'csv', 'npy' or 'mmap'; sessions: list of (n_i, d) arrays
    Shards(root, fmt) .load() (reads what the format requires) .window(s, start, T) .lengths
    WindowSampler(lengths, T, horizon, batch, seed) .next() -> (sessions, starts) ; .state() ; .set_state(state)
    make_batch(shards, sessions, starts, T, horizon, target_col) -> (X (b, T*d), y (b,))   one window at a time
    make_batch_vec(...) -> the same batch from a memory-mapped store in one gather
    train(model, shards, sampler, steps, lr, accumulate, bf16, T, horizon, target_col, opt, start_step) -> losses
    data_parallel_grads(model, X, y, n_shards) -> gradients averaged over shards (an all-reduce, in one process)
    save_checkpoint(path, model, opt, sampler, step) ; load_checkpoint(path, model, opt, sampler) -> step
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import torch
from torch import nn


def write_shards(sessions, root, fmt):
    root = pathlib.Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if fmt == "mmap":
        data = np.concatenate(sessions).astype(np.float32)
        mm = np.memmap(root / "data.f32", dtype=np.float32, mode="w+", shape=data.shape)
        mm[:] = data
        mm.flush()
        offs = np.r_[0, np.cumsum([len(s) for s in sessions])].tolist()
        (root / "index.json").write_text(json.dumps({"shape": list(data.shape), "offsets": offs}))
        return
    for i, s in enumerate(sessions):
        if fmt == "csv":
            np.savetxt(root / f"s{i:03d}.csv", s, delimiter=",", fmt="%.6g")
        else:
            np.save(root / f"s{i:03d}.npy", s.astype(np.float32))


class Shards:
    """A view of the stored sessions. load() does what one pass of training must do for the format: parse every CSV
    file, read every NumPy file into memory, or map the single file (no read until a window is touched)."""

    def __init__(self, root, fmt):
        self.root, self.fmt = pathlib.Path(root), fmt
        self.load()

    def load(self):
        if self.fmt == "mmap":
            idx = json.loads((self.root / "index.json").read_text())
            self.mm = np.memmap(self.root / "data.f32", dtype=np.float32, mode="r", shape=tuple(idx["shape"]))
            self.offsets = idx["offsets"]
            self.lengths = np.diff(self.offsets)
        else:
            files = sorted(self.root.glob(f"s*.{self.fmt}"))
            if self.fmt == "csv":
                self.data = [np.loadtxt(f, delimiter=",", dtype=np.float32) for f in files]
            else:
                self.data = [np.load(f) for f in files]
            self.lengths = np.array([len(d) for d in self.data])
        return self

    def window(self, s, start, T):
        if self.fmt == "mmap":
            a = self.offsets[s] + start
            return np.asarray(self.mm[a:a + T])
        return self.data[s][start:start + T]


class WindowSampler:
    """Uniform over (session, start) with the window and its target horizon inside one session."""

    def __init__(self, lengths, T=20, horizon=10, batch=256, seed=0):
        self.lengths, self.T, self.h, self.batch = np.asarray(lengths), T, horizon, batch
        valid = np.maximum(self.lengths - T - horizon + 1, 0)
        self.cum = np.r_[0, np.cumsum(valid)]
        self.rng = np.random.default_rng(seed)

    def next(self):
        k = self.rng.integers(0, self.cum[-1], self.batch)
        s = np.searchsorted(self.cum, k, side="right") - 1
        return s, k - self.cum[s]

    def state(self):
        return self.rng.bit_generator.state

    def set_state(self, st):
        self.rng.bit_generator.state = st


def make_batch(shards, sessions, starts, T=20, horizon=10, target_col=0):
    """Features: the window of T rows, flattened. Target: the change of column target_col over the next `horizon`
    rows after the window."""
    X, y = [], []
    for s, a in zip(sessions, starts, strict=True):
        w = shards.window(int(s), int(a), T + horizon)
        X.append(w[:T].ravel())
        y.append(w[T + horizon - 1, target_col] - w[T - 1, target_col])
    return torch.as_tensor(np.stack(X), dtype=torch.float32), torch.as_tensor(np.array(y), dtype=torch.float32)


def make_batch_vec(shards, sessions, starts, T=20, horizon=10, target_col=0):
    """The same batch as make_batch from a memory-mapped store, in one gather: row indices for every window at once."""
    rows = (np.asarray(shards.offsets)[sessions] + starts)[:, None] + np.arange(T + horizon)[None, :]
    w = np.asarray(shards.mm[rows.ravel()]).reshape(len(starts), T + horizon, -1)
    X = w[:, :T].reshape(len(starts), -1)
    y = w[:, T + horizon - 1, target_col] - w[:, T - 1, target_col]
    return torch.as_tensor(X, dtype=torch.float32), torch.as_tensor(y, dtype=torch.float32)


def train(model, shards, sampler, steps, lr=1e-3, accumulate=1, bf16=False, T=20, horizon=10, target_col=0, opt=None,
          start_step=0, scale=None):
    """Adam on mean squared error. With accumulate = k, each optimiser step sums the gradients of k micro-batches (each
    scaled by 1/k): the same step as one batch k times larger. With bf16, the forward pass runs under CPU bfloat16
    autocast (matrix products in bfloat16, the loss and the update in float32)."""
    torch.set_num_threads(1)
    opt = opt or torch.optim.Adam(model.parameters(), lr=lr)
    losses = []
    for _ in range(start_step, steps):
        opt.zero_grad()
        tot = 0.0
        for _ in range(accumulate):
            X, y = make_batch(shards, *sampler.next(), T, horizon, target_col)
            if scale is not None:
                X = (X - scale[0]) / scale[1]
            with torch.autocast("cpu", dtype=torch.bfloat16, enabled=bf16):
                p = model(X)[:, 0]
            loss = ((p.float() - y) ** 2).mean() / accumulate
            loss.backward()
            tot += float(loss.detach())
        opt.step()
        losses.append(tot)
    return losses


def data_parallel_grads(model, X, y, n_shards=2):
    """Each 'worker' computes the gradient of its shard's mean loss; the all-reduce averages them. With equal shards
    this equals the gradient of the whole batch's mean loss."""
    grads = None
    for Xs, ys in zip(torch.chunk(X, n_shards), torch.chunk(y, n_shards), strict=True):
        model.zero_grad()
        ((model(Xs)[:, 0] - ys) ** 2).mean().backward()
        g = [p.grad.detach().clone() for p in model.parameters()]
        grads = g if grads is None else [a + b for a, b in zip(grads, g, strict=True)]
    return [g / n_shards for g in grads]


def save_checkpoint(path, model, opt, sampler, step):
    torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sampler": sampler.state(), "step": step,
                "torch_rng": torch.get_rng_state()}, path)


def load_checkpoint(path, model, opt, sampler):
    ck = torch.load(path, weights_only=False)
    model.load_state_dict(ck["model"])
    opt.load_state_dict(ck["opt"])
    sampler.set_state(ck["sampler"])
    torch.set_rng_state(ck["torch_rng"])
    return ck["step"]


def mlp(d_in, hidden=64):
    return nn.Sequential(nn.Linear(d_in, hidden), nn.ReLU(), nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))
