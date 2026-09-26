"""firm.mlinfer -- models compiled for low-latency inference (Book 12, chapter 26).

Two model families leave Python here. A LightGBM forest is exported to flat node arrays (feature, threshold, left child,
right child, leaf value; a negative child is a leaf) that a loop walks, and to generated C++ with one nested branch per
node. A small multilayer perceptron is quantised to int8 (symmetric, per-tensor scales; int32 accumulation; the
activation requantised between layers with a fixed-point multiplier), after training (post-training quantisation) or
with simulated quantisation during fine-tuning (quantisation-aware training). The integer forward pass here is the
reference that cpp/mlinfer.hpp and rust/src/lib.rs reproduce bit for bit on shared test vectors in data/.

API (stable):
    export_forest(model) -> dict of numpy arrays (feature, threshold, left, right, value, roots)
    forest_predict(forest, X) -> predictions (the loop the C++ and Rust kernels run)
    write_forest(forest, path) / read_forest(path)          plain text, one array per line
    cpp_branches(forest, name) -> C++ source of a function double name(const double* x)
    MLP(d, h1, h2) ; fit_mlp(model, X, y, epochs, seed, qat) ; quantise(model, X_calib) -> dict of int arrays and
    fixed-point multipliers ; int8_forward(q, X) -> float predictions (the integer reference) ; write_mlp(q, path)
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn

# ---------------------------------------------------------------------------------------------------- trees


def export_forest(model):
    """Flatten LightGBM's dump: node ids are global; children >= 0 are nodes, < 0 are ~leaf index into `value`."""
    dump = model.booster_.dump_model()
    feat, thr, left, right, value, roots = [], [], [], [], [], []

    def walk(n):
        if "leaf_value" in n:
            value.append(n["leaf_value"])
            return -len(value)                                          # -1 .. -L: leaf index = -c - 1
        i = len(feat)
        feat.append(n["split_feature"])
        thr.append(n["threshold"])
        left.append(0)
        right.append(0)
        left[i] = walk(n["left_child"])
        right[i] = walk(n["right_child"])
        return i

    for t in dump["tree_info"]:
        roots.append(walk(t["tree_structure"]))
    return {"feature": np.array(feat, dtype=np.int32), "threshold": np.array(thr, dtype=np.float64),
            "left": np.array(left, dtype=np.int32), "right": np.array(right, dtype=np.int32),
            "value": np.array(value, dtype=np.float64), "roots": np.array(roots, dtype=np.int32)}


def forest_predict(f, X):
    """For each row: start at each tree's root, go left when x[feature] <= threshold, add the leaf's value; trees in
    order, sums in double precision, as LightGBM does."""
    X = np.atleast_2d(X)
    out = np.zeros(len(X))
    for r, x in enumerate(X):
        s = 0.0
        for root in f["roots"]:
            n = int(root)
            while n >= 0:
                n = int(f["left"][n] if x[f["feature"][n]] <= f["threshold"][n] else f["right"][n])
            s += f["value"][-n - 1]
        out[r] = s
    return out


def write_forest(f, path):
    with open(path, "w") as fh:
        for k in ("roots", "feature", "left", "right"):
            fh.write(k + " " + " ".join(str(int(v)) for v in f[k]) + "\n")
        for k in ("threshold", "value"):
            fh.write(k + " " + " ".join(repr(float(v)) for v in f[k]) + "\n")


def read_forest(path):
    out = {}
    for line in open(path):
        k, *v = line.split()
        out[k] = np.array(v, dtype=np.float64 if k in ("threshold", "value") else np.int32)
    return out


def cpp_branches(f, name="forest_branches"):
    """One C++ function per forest: each tree an if/else nest with the thresholds as literals."""
    lines = [f"inline double {name}(const double* x) {{", "  double s = 0.0;"]

    def emit(n, ind):
        pad = "  " * ind
        if n < 0:
            lines.append(f"{pad}s += {float(f['value'][-n - 1])!r};")
            return
        lines.append(f"{pad}if (x[{int(f['feature'][n])}] <= {float(f['threshold'][n])!r}) {{")
        emit(int(f["left"][n]), ind + 1)
        lines.append(f"{pad}}} else {{")
        emit(int(f["right"][n]), ind + 1)
        lines.append(f"{pad}}}")

    for root in f["roots"]:
        emit(int(root), 1)
    lines += ["  return s;", "}"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------------------- int8 MLP
class MLP(nn.Module):
    def __init__(self, d=16, h1=32, h2=16):
        super().__init__()
        self.l1, self.l2, self.l3 = nn.Linear(d, h1), nn.Linear(h1, h2), nn.Linear(h2, 1)
        self.qat, self.qmax = False, 127

    def _fq(self, x, scale):
        """Fake quantisation: round to the integer grid of `scale` in the forward pass, pass the gradient straight."""
        q = torch.clamp(torch.round(x / scale), -self.qmax, self.qmax) * scale
        return x + (q - x).detach()

    def forward(self, x):
        layers = (self.l1, self.l2, self.l3)
        for i, lin in enumerate(layers):
            w = lin.weight
            if self.qat:
                w = self._fq(w, w.detach().abs().max() / self.qmax)
                x = self._fq(x, x.detach().abs().max() / self.qmax)
            x = nn.functional.linear(x, w, lin.bias)
            if i < 2:
                x = torch.relu(x)
        return x[:, 0]


def fit_mlp(model, X, y, epochs=60, seed=0, qat=False, lr=3e-3, batch=256, bits=8):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    if not qat:                                                          # initial weights from the seed alone
        for lin in (model.l1, model.l2, model.l3):
            lin.reset_parameters()
    g = torch.Generator().manual_seed(seed)
    Xt, yt = torch.as_tensor(X, dtype=torch.float32), torch.as_tensor(y, dtype=torch.float32)
    model.qat, model.qmax = qat, 2 ** (bits - 1) - 1
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(epochs):
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), batch):
            b = perm[i:i + batch]
            opt.zero_grad()
            ((model(Xt[b]) - yt[b]) ** 2).mean().backward()
            opt.step()
    model.qat = False
    return model


def _multiplier(m):
    """A real multiplier m in (0, 1) as an int32 fixed-point value and a right shift: m ~ M * 2^-shift, M < 2^31."""
    shift = 0
    while m < 0.5:
        m *= 2
        shift += 1
    M = int(round(m * (1 << 31)))
    if M == 1 << 31:
        M //= 2
        shift -= 1
    return M, shift + 31


def quantise(model, X_calib, bits=8):
    """Symmetric int8: weights per tensor (scale = max|w| / 127), inputs and hidden activations per tensor from the
    calibration data, biases in int32 at the product scale, and between layers a fixed-point multiplier that maps the
    int32 accumulator back to int8."""
    with torch.no_grad():
        x = torch.as_tensor(X_calib, dtype=torch.float32)
        acts = [float(x.abs().max())]
        h = x
        for i, lin in enumerate((model.l1, model.l2, model.l3)):
            h = lin(h)
            if i < 2:
                h = torch.relu(h)
                acts.append(float(h.abs().max()))
    qm = 2 ** (bits - 1) - 1
    s_in = [a / qm for a in acts]
    q = {"s_in": s_in[0], "layers": [], "qmax": qm}
    for i, lin in enumerate((model.l1, model.l2, model.l3)):
        w = lin.weight.detach().numpy().astype(np.float64)
        sw = np.abs(w).max() / qm
        W = np.clip(np.round(w / sw), -qm, qm).astype(np.int32)
        sa = s_in[i]
        B = np.round(lin.bias.detach().numpy() / (sa * sw)).astype(np.int64).astype(np.int32)
        layer = {"W": W, "B": B, "prod": sa * sw}
        if i < 2:
            layer["M"], layer["shift"] = _multiplier(sa * sw / s_in[i + 1])
        q["layers"].append(layer)
    return q


def _requant(acc, M, shift, qm=127):
    """round(acc * M / 2^shift) with integer arithmetic (rounding half away from zero), then clamp to the grid."""
    p = acc.astype(np.int64) * M
    r = (np.abs(p) + (1 << (shift - 1))) >> shift
    return np.clip(np.sign(p) * r, -qm, qm)


def int8_forward(q, X):
    """The integer reference: int8 inputs, int32 accumulators, fixed-point requantisation, ReLU as max(0, .); the last
    layer's accumulator is scaled back to a float."""
    qm = q.get("qmax", 127)
    x = np.clip(np.round(np.asarray(X, dtype=np.float64) / q["s_in"]), -qm, qm).astype(np.int64)
    for i, L in enumerate(q["layers"]):
        acc = x @ L["W"].T.astype(np.int64) + L["B"].astype(np.int64)
        if i < 2:
            x = np.maximum(_requant(acc, L["M"], L["shift"], qm), 0)
        else:
            return acc[:, 0].astype(np.float64) * L["prod"]
    return None


def write_mlp(q, path):
    with open(path, "w") as fh:
        fh.write(f"s_in {float(q['s_in'])!r}\n")
        for L in q["layers"]:
            n_out, n_in = L["W"].shape
            fh.write(f"layer {n_out} {n_in} {L.get('M', 0)} {L.get('shift', 0)} {float(L['prod'])!r}\n")
            fh.write("W " + " ".join(str(int(v)) for v in L["W"].ravel()) + "\n")
            fh.write("B " + " ".join(str(int(v)) for v in L["B"]) + "\n")
