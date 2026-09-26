"""Training infrastructure (One Quant Book 12, chapter 23).

Eight ten-minute firm.tape sessions become per-session tables of 41 columns (the mid price in ticks and the ten-level
book snapshot of chapter 8, every half second), stored as CSV, NumPy and memory-mapped shards. A small network learns
the mid's change over the next ten snapshots from the last twenty. The deterministic experiments: bfloat16 autocast
against float32, gradient accumulation against a larger batch, a data-parallel step (simulated all-reduce) against one
process, and a run killed and resumed from a checkpoint against an uninterrupted one. Timings are in bench_train.py,
measured once on the author's laptop; the tests check only what does not depend on the machine."""
from __future__ import annotations

import copy
import functools
import os
import pathlib
import sys
import tempfile

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("mltrain", "lobseq", "tape"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_lobseq import snapshots  # noqa: E402
from firm_mltrain import (  # noqa: E402
    Shards,
    WindowSampler,
    data_parallel_grads,
    load_checkpoint,
    make_batch,
    make_batch_vec,
    mlp,
    save_checkpoint,
    train,
    write_shards,
)
from firm_tape import TapeConfig, simulate  # noqa: E402

N_SESSIONS, SECONDS, T, H = 8, 600.0, 20, 10


@functools.lru_cache(maxsize=1)
def sessions():
    out = []
    for s in range(N_SESSIONS):
        tape = simulate(TapeConfig(seconds=SECONDS, news_at=None, seed=500 + s))
        _, S, mid = snapshots(tape, step=0.5)
        out.append(np.column_stack([mid, S]).astype(np.float32))
    return out


@functools.lru_cache(maxsize=1)
def shard_root():
    root = pathlib.Path(tempfile.mkdtemp(prefix="oqb12_ch23_"))
    for fmt in ("csv", "npy", "mmap"):
        write_shards(sessions(), root / fmt, fmt)
    return root


def shards(fmt="mmap"):
    return Shards(shard_root() / fmt, fmt)


@functools.lru_cache(maxsize=1)
def scale():
    X = np.concatenate([s for s in sessions()])
    mu, sd = X.mean(0), X.std(0) + 1e-6
    return torch.as_tensor(np.tile(mu, T)), torch.as_tensor(np.tile(sd, T))


def fresh(seed=0):
    torch.manual_seed(seed)
    return mlp(T * sessions()[0].shape[1])


def run(steps=300, bf16=False, accumulate=1, batch=256, seed=0):
    torch.use_deterministic_algorithms(True)
    model = fresh(seed)
    sh = shards()
    smp = WindowSampler(sh.lengths, T, H, batch, seed=seed)
    return model, train(model, sh, smp, steps, 1e-3, accumulate, bf16, T, H, 0, scale=scale())


@functools.lru_cache(maxsize=1)
def precision():
    """Losses of the same run in float32 and under bfloat16 autocast: the largest absolute difference over 300 steps,
    and the mean losses of the last 50 steps."""
    _, l32 = run(bf16=False)
    _, l16 = run(bf16=True)
    l32, l16 = np.array(l32), np.array(l16)
    return {"max diff": float(np.abs(l32 - l16).max()), "max rel diff": float(np.max(np.abs(l32 - l16) / l32)),
            "last 50 fp32": float(l32[-50:].mean()), "last 50 bf16": float(l16[-50:].mean()),
            "first": float(l32[0])}


def accumulation():
    """Four micro-batches of 64 accumulated against one batch of 256 drawn by the same sampler: largest parameter
    difference after 20 steps (a sampler that yields the same 256 windows either way)."""
    class Split:
        def __init__(self, smp, k):
            self.smp, self.k, self.buf = smp, k, []

        def next(self):
            if not self.buf:
                s, a = self.smp.next()
                self.buf = list(zip(np.array_split(s, self.k), np.array_split(a, self.k), strict=True))
            return self.buf.pop(0)

    sh = shards()
    torch.use_deterministic_algorithms(True)
    m1, m2 = fresh(0), fresh(0)
    train(m1, sh, WindowSampler(sh.lengths, T, H, 256, seed=3), 20, scale=scale())
    train(m2, sh, Split(WindowSampler(sh.lengths, T, H, 256, seed=3), 4), 20, accumulate=4, scale=scale())
    return max(float((a - b).abs().max()) for a, b in zip(m1.parameters(), m2.parameters(), strict=True))


def data_parallel():
    """Gradient of one batch of 256 against the average of two workers' gradients on halves of it."""
    sh = shards()
    model = fresh(0)
    X, y = make_batch(sh, *WindowSampler(sh.lengths, T, H, 256, seed=4).next(), T, H, 0)
    X = (X - scale()[0]) / scale()[1]
    g2 = data_parallel_grads(model, X, y, 2)
    g1 = data_parallel_grads(model, X, y, 1)
    return max(float((a - b).abs().max()) for a, b in zip(g1, g2, strict=True)), max(float(a.abs().max()) for a in g1)


def resume(steps=200, kill_at=100):
    """An uninterrupted run against one killed at step 100 and resumed from its checkpoint into fresh objects."""
    torch.use_deterministic_algorithms(True)
    sh = shards()
    ref = fresh(0)
    opt = torch.optim.Adam(ref.parameters(), lr=1e-3)
    l_ref = train(ref, sh, WindowSampler(sh.lengths, T, H, 256, seed=9), steps, opt=opt, scale=scale())
    m = fresh(0)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    smp = WindowSampler(sh.lengths, T, H, 256, seed=9)
    l_a = train(m, sh, smp, kill_at, opt=opt, scale=scale())
    path = shard_root() / "ckpt.pt"
    save_checkpoint(path, m, opt, smp, kill_at)
    m2 = fresh(123)                                                     # another initialisation: must be overwritten
    opt2 = torch.optim.Adam(m2.parameters(), lr=1e-3)
    smp2 = WindowSampler(sh.lengths, T, H, 256, seed=777)
    step = load_checkpoint(path, m2, opt2, smp2)
    l_b = train(m2, sh, smp2, steps, opt=opt2, start_step=step, scale=scale())
    same = all(torch.equal(a, b) for a, b in zip(ref.parameters(), m2.parameters(), strict=True))
    return same, l_ref == l_a + l_b, path.stat().st_size


def naive_resume(steps=200, kill_at=100):
    """The same kill with only the model's weights saved: the optimiser restarts and the sampler repeats its windows."""
    sh = shards()
    ref = fresh(0)
    opt = torch.optim.Adam(ref.parameters(), lr=1e-3)
    train(ref, sh, WindowSampler(sh.lengths, T, H, 256, seed=9), steps, opt=opt, scale=scale())
    m = fresh(0)
    train(m, sh, WindowSampler(sh.lengths, T, H, 256, seed=9), kill_at, scale=scale())
    w = copy.deepcopy(m.state_dict())
    m2 = fresh(0)
    m2.load_state_dict(w)
    train(m2, sh, WindowSampler(sh.lengths, T, H, 256, seed=9), steps - kill_at, scale=scale())
    return max(float((a - b).abs().max()) for a, b in zip(ref.parameters(), m2.parameters(), strict=True))


def sizes():
    root = shard_root()
    return {fmt: sum(f.stat().st_size for f in (root / fmt).iterdir()) for fmt in ("csv", "npy", "mmap")}


def gather_parity():
    """The one-gather batch equals the window-by-window batch."""
    sh = shards()
    s, a = WindowSampler(sh.lengths, T, H, 256, seed=5).next()
    X1, y1 = make_batch(sh, s, a, T, H, 0)
    X2, y2 = make_batch_vec(sh, s, a, T, H, 0)
    return bool(torch.equal(X1, X2) and torch.equal(y1, y2))
