import pathlib
import sys

import numpy as np
import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
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

rng = np.random.default_rng(0)
SESS = [np.column_stack([np.arange(n) + 1000 * i, rng.standard_normal((n, 2))]).astype(np.float32)
        for i, n in enumerate((50, 80, 65))]


def _all(tmp_path):
    for fmt in ("csv", "npy", "mmap"):
        write_shards(SESS, tmp_path / fmt, fmt)
    return {fmt: Shards(tmp_path / fmt, fmt) for fmt in ("csv", "npy", "mmap")}


def test_formats_agree_and_windows_stay_in_sessions(tmp_path):
    sh = _all(tmp_path)
    smp = WindowSampler(sh["mmap"].lengths, T=5, horizon=3, batch=500, seed=1)
    s, a = smp.next()
    for fmt in ("csv", "npy"):
        X1, y1 = make_batch(sh[fmt], s, a, 5, 3, 0)
        X2, y2 = make_batch(sh["mmap"], s, a, 5, 3, 0)
        assert torch.allclose(X1, X2, atol=1e-4) and torch.allclose(y1, y2, atol=1e-3)
    X, y = make_batch(sh["mmap"], s, a, 5, 3, 0)
    assert torch.all(y == 3.0)                                          # the first column counts rows: horizon 3
    Xv, yv = make_batch_vec(sh["mmap"], s, a, 5, 3, 0)
    assert torch.equal(X, Xv) and torch.equal(y, yv)


def test_accumulation_equals_large_batch_and_allreduce(tmp_path):
    sh = _all(tmp_path)["mmap"]
    torch.manual_seed(0)
    model = mlp(15, 8)
    X, y = make_batch(sh, *WindowSampler(sh.lengths, 5, 3, 64, seed=2).next(), 5, 3, 0)
    g1, g4 = data_parallel_grads(model, X, y, 1), data_parallel_grads(model, X, y, 4)
    assert all(torch.allclose(a, b, atol=1e-6) for a, b in zip(g1, g4, strict=True))


def test_bitwise_resume(tmp_path):
    sh = _all(tmp_path)["mmap"]
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(0)
    ref = mlp(15, 8)
    opt = torch.optim.Adam(ref.parameters(), lr=1e-2)
    train(ref, sh, WindowSampler(sh.lengths, 5, 3, 32, seed=3), 30, opt=opt, T=5, horizon=3)
    torch.manual_seed(0)
    m = mlp(15, 8)
    opt = torch.optim.Adam(m.parameters(), lr=1e-2)
    smp = WindowSampler(sh.lengths, 5, 3, 32, seed=3)
    train(m, sh, smp, 12, opt=opt, T=5, horizon=3)
    save_checkpoint(tmp_path / "c.pt", m, opt, smp, 12)
    m2 = mlp(15, 8)
    opt2 = torch.optim.Adam(m2.parameters(), lr=1e-2)
    smp2 = WindowSampler(sh.lengths, 5, 3, 32, seed=99)
    step = load_checkpoint(tmp_path / "c.pt", m2, opt2, smp2)
    train(m2, sh, smp2, 30, opt=opt2, start_step=step, T=5, horizon=3)
    assert all(torch.equal(a, b) for a, b in zip(ref.parameters(), m2.parameters(), strict=True))
