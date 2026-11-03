"""Every number printed in the answers of "Machine Learning": exact values and direct runs on simulated data."""
import math

import numpy as np
from scipy import optimize, stats
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor

NONNUMERIC = {29: "judgement on which features leak; no number to compute"}


def test_q1():
    tp, fp, fn = 40, 60, 10
    tn = 1000 - tp - fp - fn
    assert tn == 890
    assert (tp + tn) / 1000 == 0.93
    prec, rec = tp / (tp + fp), tp / (tp + fn)
    assert prec == 0.4 and rec == 0.8
    assert round(2 * prec * rec / (prec + rec), 3) == 0.533
    assert (fp + tn) / 1000 == 0.95
    assert tp / (tp + 0.5 * (fp + fn)) == 2 * prec * rec / (prec + rec)


def test_q2():
    cdf = stats.binom.cdf(np.arange(0, 101), 100, 0.5)
    pmf_max = np.diff(np.concatenate([[0], cdf**20]))
    e = (pmf_max * np.arange(0, 101)).sum()
    assert abs(e - 59.3) < 0.15
    assert abs(50 + 1.867 * 5 - 59.3) < 0.1
    rng = np.random.default_rng(2)
    assert abs(rng.binomial(100, 0.5, (200_000, 20)).max(axis=1).mean() - e) < 0.05


def test_q3():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(300, 3)) * [1.0, 1.0, 1.0]
    y = x[:, 0] + np.sin(x[:, 1]) + rng.normal(size=300)
    z = x.copy()
    z[:, 0] *= 100
    t = rng.normal(size=(50, 3))
    tz = t.copy()
    tz[:, 0] *= 100

    def same(model):
        a = model.fit(x, y).predict(t)
        b = model.fit(z, y).predict(tz)
        return np.allclose(a, b, atol=1e-7)

    assert same(LinearRegression())
    assert not same(Ridge(alpha=10.0))
    assert not same(KNeighborsRegressor(5))
    assert same(DecisionTreeRegressor(max_depth=4, random_state=0))

    def pcr(data, tdata):
        mean = data.mean(0)
        _, _, vt = np.linalg.svd(data - mean, full_matrices=False)
        f = (data - mean) @ vt[:2].T
        return LinearRegression().fit(f, y).predict((tdata - mean) @ vt[:2].T)

    assert not np.allclose(pcr(x, t), pcr(z, tz), atol=1e-3)


def test_q4():
    h = -(0.1 * math.log(0.1) + 0.9 * math.log(0.9))
    assert round(h, 3) == 0.325
    assert round(math.log(2), 3) == 0.693
    assert round(-math.log(0.001), 2) == 6.91
    # One such row in 100 adds 0.069, a fifth of the base loss.
    assert round(6.91 / 100, 3) == 0.069
    # The constant minimising log loss is the base rate.
    r = optimize.minimize_scalar(lambda p: -(0.1 * math.log(p) + 0.9 * math.log(1 - p)), bounds=(0.01, 0.99), method="bounded")
    assert abs(r.x - 0.1) < 1e-4


def test_q5():
    k = math.exp(0.7)
    assert round(k, 2) == 2.01
    a = 0.25 * k / (1 + 0.25 * k)
    b = k / (1 + k)
    assert round(a, 2) == 0.33
    assert round(b, 2) == 0.67
    # The steepest change is at 0.5, with slope coef / 4.
    assert abs((b - 0.5) / 0.7 - 0.25) < 0.02


def test_q6():
    assert 1000 * 4 // 5 == 800
    assert 10**3 == 1000 and 10**3 * 5 == 5000
    idx = np.arange(1000)
    rng = np.random.default_rng(6)
    rng.shuffle(idx)
    folds = np.array_split(idx, 5)
    val = np.zeros(1000, int)
    trn = np.zeros(1000, int)
    for i, f in enumerate(folds):
        val[f] += 1
        trn[np.concatenate([g for j, g in enumerate(folds) if j != i])] += 1
    assert (val == 1).all() and (trn == 4).all()
    assert {len(np.concatenate([g for j, g in enumerate(folds) if j != i])) for i in range(5)} == {800}


def test_q7():
    def precision(prev, tpr, fpr):
        return prev * tpr / (prev * tpr + (1 - prev) * fpr)

    assert round(precision(0.01, 0.9, 0.05), 3) == 0.154
    assert round(precision(0.01, 0.9, 0.01), 3) == 0.476
    assert round(precision(0.10, 0.9, 0.05), 3) == 0.667
    # AUC is the same in a run with either prevalence.
    rng = np.random.default_rng(7)
    pos = rng.normal(2, 1, 4000)
    for n in (400_000, 40_000):
        neg = rng.normal(0, 1, n)
        all_scores = np.concatenate([pos, neg])
        ranks = stats.rankdata(all_scores)
        auc = (ranks[:4000].sum() - 4000 * 4001 / 2) / (4000 * n)
        assert abs(auc - stats.norm.cdf(2 / math.sqrt(2))) < 0.01


def test_q8():
    assert (20 + 1) * 64 + (64 + 1) * 32 + (32 + 1) * 1 == 3457
    assert 20 * 64 + 64 * 32 + 32 == 3360
    assert round(3457 / 1250, 1) == 2.8
    import torch

    torch.set_num_threads(1)
    net = torch.nn.Sequential(
        torch.nn.Linear(20, 64), torch.nn.ReLU(), torch.nn.Linear(64, 32), torch.nn.ReLU(), torch.nn.Linear(32, 1)
    )
    assert sum(p.numel() for p in net.parameters()) == 3457


def _knn_scores(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-3, 3, n)[:, None]
    y = (np.sin(2 * x[:, 0]) > 0).astype(int)
    flip = rng.random(n) < 0.1
    y = np.where(flip, 1 - y, y)
    return x, y


def test_q9():
    xt, yt = _knn_scores(5000, 91)
    from sklearn.neighbors import KNeighborsClassifier

    gaps = []
    for n in (50, 2000):
        x, y = _knn_scores(n, 90 + n)
        m = KNeighborsClassifier(1).fit(x, y)
        gaps.append(m.score(x, y) - m.score(xt, yt))
    # High variance: more data narrows the gap.
    assert gaps[1] < gaps[0]
    # High bias: a linear model on a wave stays low on both, whatever the data.
    low = []
    for n in (50, 2000):
        x, y = _knn_scores(n, 190 + n)
        m = LogisticRegression().fit(x, y)
        low.append((m.score(x, y), m.score(xt, yt)))
    assert max(low[1]) < 0.7 and abs(low[1][0] - low[1][1]) < 0.05


def test_q10():
    def mse(k, d):
        return 1 / k + (d * (k + 1) / 2) ** 2

    v = {k: mse(k, 0.2) for k in range(1, 8)}
    assert min(v, key=v.get) == 3
    assert round(v[1], 2) == 1.04 and round(v[3], 3) == 0.493 and round(v[4], 2) == 0.5
    w = {k: mse(k, 0.1) for k in range(1, 12)}
    assert min(w, key=w.get) == 6
    assert round(w[6], 3) == 0.289
    rng = np.random.default_rng(10)
    obs = 0.2 * np.arange(1, 4) + rng.normal(size=(2_000_000, 3))
    assert abs(((obs.mean(axis=1)) ** 2).mean() - v[3]) < 0.002


def test_q11():
    rng = np.random.default_rng(11)
    n, p = 100, 20
    x = rng.normal(size=(n, p))
    h = x @ np.linalg.solve(x.T @ x, x.T)
    tr, te = [], []
    for _ in range(4000):
        e = rng.normal(size=n)
        fit = h @ e
        tr.append(((e - fit) ** 2).mean())
        te.append(((rng.normal(size=n) - fit) ** 2).mean())
    assert abs(np.mean(tr) - 0.8) < 0.01
    assert abs(np.mean(te) - 1.2) < 0.01


def _gini(a, b):
    p = a / (a + b)
    return 2 * p * (1 - p)


def _ent(a, b):
    return sum(-x / (a + b) * math.log2(x / (a + b)) for x in (a, b) if x)


def test_q12():
    g0 = _gini(40, 60)
    g = 0.4 * _gini(30, 10) + 0.6 * _gini(10, 50)
    assert round(g0, 2) == 0.48 and round(_gini(30, 10), 3) == 0.375 and round(_gini(10, 50), 3) == 0.278
    assert round(g0 - g, 3) == 0.163
    e0 = _ent(40, 60)
    e = 0.4 * _ent(30, 10) + 0.6 * _ent(10, 50)
    assert round(e0, 3) == 0.971 and round(_ent(30, 10), 3) == 0.811 and round(_ent(10, 50), 3) == 0.650
    assert round(e0 - e, 3) == 0.256


def test_q13():
    a = (min(300, 100) + min(100, 300)) / 800
    b = (min(200, 400) + 0) / 800
    assert a == b == 0.25
    assert _gini(300, 100) == 0.375
    assert round(600 / 800 * _gini(200, 400), 3) == 0.333
    # Concavity: at the same mixing weights Gini sits above the chord, error does not.
    assert _gini(1, 1) > 0.5 * (_gini(3, 1) + _gini(1, 3))

    def err(c, d):
        return (min(c, d) + min(400 - c, 400 - d)) / 800

    def gin(c, d):
        return ((c + d) * _gini(c, d) + (800 - c - d) * _gini(400 - c, 400 - d)) / 800

    # A split with no tie: the two criteria rank it and A in opposite order.
    assert err(210, 400) == 0.2625 and err(210, 400) > err(300, 100)
    assert round(gin(210, 400), 3) == 0.344 and gin(210, 400) < gin(300, 100)
    # They usually agree: over every pair of splits on a grid, few are ranked in opposite order, all near ties.
    splits = [(c, d) for c in range(0, 401, 20) for d in range(0, 401, 20) if 0 < c + d < 800]
    es = np.array([err(c, d) for c, d in splits])
    gs = np.array([gin(c, d) for c, d in splits])
    i, j = np.triu_indices(len(splits), 1)
    de, dg = es[i] - es[j], gs[i] - gs[j]
    strict = (np.abs(de) > 1e-12) & (np.abs(dg) > 1e-12)
    opposite = strict & (np.sign(de) != np.sign(dg))
    assert 0 < opposite.sum() < 0.05 * strict.sum()
    assert np.abs(de[opposite]).max() < 0.07
    # Ties are frequent near the root: with a weak signal both children keep the parent's majority.
    rng = np.random.default_rng(13)
    x = rng.standard_normal(2000)
    y = rng.random(2000) < 0.4 + 0.05 * np.tanh(x)
    wrong = min(y.sum(), (~y).sum())
    ties = 0
    for q in range(5, 96, 5):
        left = x < np.quantile(x, q / 100)
        kids = [y[left], y[~left]]
        ties += sum(min(k.sum(), (~k).sum()) for k in kids) == wrong
    assert ties >= 10


def test_q14():
    assert round(0.3 + 0.7 / 100, 3) == 0.307
    assert round(1.2 * 0.1 + 1.2 * 0.9 / 100, 4) == 0.1308
    rng = np.random.default_rng(14)
    common = rng.normal(size=(40_000, 1))
    own = rng.normal(size=(40_000, 100))
    x = math.sqrt(0.3) * common + math.sqrt(0.7) * own
    assert abs(x.mean(axis=1).var() - 0.307) < 0.01


def test_q15():
    assert 1 - 0.9**21 < 0.9 < 1 - 0.9**22
    assert 1 - 0.9**43 < 0.99 < 1 - 0.9**44
    y = 1.0
    f = 0.0
    for _ in range(22):
        f += 0.1 * (y - f)
    assert abs(f - (1 - 0.9**22)) < 1e-12
    # Follow-up: noise fitted by a single full step, against shrunken steps with fresh noisy estimates.
    rng = np.random.default_rng(15)
    noise = rng.normal(size=(200_000, 44))
    g = np.zeros(200_000)
    for j in range(44):
        g += 0.1 * (1 + noise[:, j] - g)
    assert abs(g.var() - 0.1 / (2 - 0.1) * (1 - 0.9 ** (2 * 44))) < 0.002
    assert round(0.1 / 1.9, 3) == 0.053


def test_q16():
    rng = np.random.default_rng(16)

    def data(n):
        x = rng.uniform(-1, 1, (n, 2))
        y = (x[:, 0] * x[:, 1] > 0).astype(int)
        flip = rng.random(n) < 0.2
        return x, np.where(flip, 1 - y, y)

    x, y = data(400)
    xt, yt = data(4000)
    gb = GradientBoostingClassifier(n_estimators=1000, learning_rate=0.5, max_depth=3, random_state=0).fit(x, y)
    errs = [1 - np.mean(p == yt) for p in gb.staged_predict(xt)]
    tr = 1 - gb.score(x, y)
    assert tr < 0.01
    assert errs[-1] > min(errs) + 0.02
    assert errs[-1] > 0.25
    rf10 = RandomForestClassifier(n_estimators=100, random_state=0).fit(x, y)
    rf = RandomForestClassifier(n_estimators=1000, random_state=0).fit(x, y)
    assert abs(rf.score(xt, yt) - rf10.score(xt, yt)) < 0.01
    assert 0.2 < 1 - rf.score(xt, yt) < 0.3
    assert rf.score(x, y) > 0.99


def test_q17():
    al = 0.5 * math.log(0.7 / 0.3)
    assert round(al, 3) == 0.424
    assert round(math.exp(al), 3) == 1.528
    assert round(math.exp(-al), 3) == 0.655
    w = 0.3 * math.exp(al)
    r = 0.7 * math.exp(-al)
    assert abs(w / (w + r) - 0.5) < 1e-12
    assert round(2 * math.sqrt(0.21), 3) == 0.917
    assert abs(w + r - 2 * math.sqrt(0.21)) < 1e-12


def test_q18():
    s2 = np.array([100.0, 10, 1])
    assert round((s2 / (s2 + 10)).sum(), 2) == 1.5
    rng = np.random.default_rng(18)
    q, _ = np.linalg.qr(rng.normal(size=(50, 3)))
    x = q * np.sqrt(s2)
    assert abs(np.trace(x @ np.linalg.solve(x.T @ x + 10 * np.eye(3), x.T)) - (s2 / (s2 + 10)).sum()) < 1e-9
    assert abs((s2 / (s2 + 1e-9)).sum() - 3) < 1e-6
    assert (s2 / (s2 + 1e9)).sum() < 1e-6
    # Posterior mean, against sampling.
    t2, v2 = 0.25, 1.0
    xx = rng.normal(size=(5, 2))
    y = rng.normal(size=5)
    post = np.linalg.solve(xx.T @ xx + v2 / t2 * np.eye(2), xx.T @ y)
    cov = np.linalg.inv(xx.T @ xx / v2 + np.eye(2) / t2)
    mean = cov @ (xx.T @ y) / v2
    assert np.allclose(post, mean)


def test_q19():
    def nll(b):
        return 2 * math.log(1 + math.exp(-b))

    assert nll(10) < nll(5) < nll(1)
    beta = optimize.brentq(lambda b: 2 / (1 + math.exp(b)) - 0.1 * b, 0.1, 10)
    assert round(beta, 2) == 2.13
    r = optimize.minimize_scalar(lambda b: nll(b) + 0.05 * b * b, bounds=(0, 10), method="bounded")
    assert abs(r.x - beta) < 1e-3
    assert round(1 / (1 + math.exp(-beta)), 2) == 0.89
    # Library with penalty lambda / 2 beta^2 corresponds to C = 1 / lambda.
    m = LogisticRegression(C=10.0, fit_intercept=False).fit([[-1.0], [1.0]], [0, 1])
    assert abs(m.coef_[0, 0] - beta) < 1e-3
    assert round(1 / (1 + math.exp(-beta)), 3) == 0.894


def test_q20():
    def post(lr):
        return lr / (1 + lr)

    assert round(post(3 * 0.1), 2) == 0.23
    assert round(post(27 * 0.1), 2) == 0.73
    assert round(post(3), 2) == 0.75
    assert round(post(27), 3) == 0.964
    # Simulate one independent feature pair and check the true posterior of the observed values.
    rng = np.random.default_rng(20)
    n = 4_000_000
    cls = rng.random(n) < 0.5
    a = rng.random(n) < np.where(cls, 0.75, 0.25)
    b = rng.random(n) < np.where(cls, 0.1, 0.5)
    # A has ratio 3, and "B true" has ratio 0.2; used only as a check on the product rule.
    obs = cls[a & b].mean()
    assert abs(obs - post(3 * 0.2)) < 0.01


def test_q21():
    def sig(z):
        return 1 / (1 + math.exp(-z))

    def loss(w1, w2):
        return 0.5 * (w2 * sig(w1)) ** 2

    w1, w2 = 0.0, 2.0
    h = sig(w1)
    yh = w2 * h
    assert h == 0.5 and yh == 1 and loss(w1, w2) == 0.5
    g2 = yh * h
    g1 = yh * w2 * h * (1 - h)
    assert g2 == 0.5 and g1 == 0.5
    e = 1e-6
    assert abs((loss(w1 + e, w2) - loss(w1 - e, w2)) / (2 * e) - g1) < 1e-8
    assert abs((loss(w1, w2 + e) - loss(w1, w2 - e)) / (2 * e) - g2) < 1e-8
    a, b = w1 - 0.1 * g1, w2 - 0.1 * g2
    assert a == -0.05 and b == 1.95
    assert round(sig(a), 4) == 0.4875
    assert round(b * sig(a), 4) == 0.9506
    assert round(loss(a, b), 4) == 0.4518


def test_q22():
    assert round(0.25**10 * 1e7, 1) == 9.5
    rng = np.random.default_rng(22)
    n = 500

    def forward(var, act, depth=30):
        x = rng.normal(size=n)
        for _ in range(depth):
            w = rng.normal(0, math.sqrt(var), (n, n))
            x = act(w @ x)
        return (x**2).mean()

    relu = lambda v: np.maximum(v, 0)  # noqa: E731
    he = forward(2 / n, relu)
    small = forward(1 / n, relu)
    big = forward(4 / n, relu)
    assert 0.1 < he < 10
    assert small < 1e-5
    assert big > 1e5


def test_q23():
    from itertools import product

    r = lambda v: max(v, 0)  # noqa: E731
    for a, b in product((0, 1), repeat=2):
        assert r(a + b) - 2 * r(a + b - 1) == (a ^ b)

    def parity(bits):
        s = sum(bits)
        v = r(s)
        for k in range(1, len(bits)):
            v += 2 * (-1) ** k * r(s - k)
        return v

    for n in (3, 4, 5):
        for bits in product((0, 1), repeat=n):
            assert parity(bits) == sum(bits) % 2
    # No line separates the classes: a brute search over a grid finds none.
    grid = np.linspace(-2, 2, 21)
    for w1 in grid:
        for w2 in grid:
            for c in grid:
                sc = [c, w1 + c, w2 + c, w1 + w2 + c]
                assert not (sc[0] < 0 and sc[3] < 0 and sc[1] > 0 and sc[2] > 0)


def test_q24():
    z = -7.0
    p = 1 / (1 + math.exp(-z))
    assert round(p, 5) == 0.00091
    ce = p - 1
    se = (p - 1) * p * (1 - p)
    assert round(ce, 3) == -0.999
    assert round(se * 1e4, 2) == -9.09
    assert round(ce / se) == 1099
    # Squared loss is concave out there: second difference is negative.
    h = 1e-3

    def sq(t):
        return 0.5 * (1 / (1 + math.exp(-t)) - 1) ** 2

    assert sq(-7 + h) - 2 * sq(-7) + sq(-7 - h) < 0
    assert sq(1 + h) - 2 * sq(1) + sq(1 - h) > 0


def test_q25():
    pos = [0.9, 0.6, 0.4]
    neg = [0.7, 0.3, 0.2, 0.1]
    cnt = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    assert cnt == 10
    assert round(cnt / 12, 3) == 0.833
    r = stats.rankdata(pos + neg)
    assert r[:3].sum() == 16
    assert (16 - 6) / 12 == cnt / 12
    # Trapezoid on the ROC.
    thr = sorted(pos + neg, reverse=True)
    tpr = [0.0] + [np.mean(np.array(pos) >= t) for t in thr]
    fpr = [0.0] + [np.mean(np.array(neg) >= t) for t in thr]
    area = sum((fpr[i + 1] - fpr[i]) * (tpr[i + 1] + tpr[i]) / 2 for i in range(len(tpr) - 1))
    assert abs(area - 10 / 12) < 1e-12


def test_q26():
    assert 1 / (1 + 9) == 0.1
    assert round(1 / 1.5, 3) == 0.667
    assert abs((2 / 3) * 0.5 - (1 / 3) * 1) < 1e-12


def test_q27():
    m = 0.52 - 0.48
    sd = math.sqrt(1 - m * m)
    assert round(m, 2) == 0.04 and round(sd, 4) == 0.9992
    assert round(m / sd * math.sqrt(252), 2) == 0.64
    assert round((m - 0.02) / sd * math.sqrt(252), 2) == 0.32
    rng = np.random.default_rng(27)
    r = np.where(rng.random(10_000_000) < 0.52, 1.0, -1.0)
    assert abs(r.mean() / r.std() * math.sqrt(252) - 0.635) < 0.02


def test_q28():
    assert 1 - 5 / 20 == 0.75
    rng = np.random.default_rng(28)
    d = rng.normal(size=1020)
    lab = np.convolve(d, np.ones(20), "valid")[:1000]
    assert abs(np.corrcoef(lab[:-5], lab[5:])[0, 1] - 0.75) < 0.2
    # Count rows that overlap a test block of 400..599.
    test = set(range(400, 600))
    train = [t for t in range(1000) if t not in test]
    clean = [t for t in train if not any(u in test for u in range(t - 19, t + 20))]
    assert len(train) - len(clean) == 38 and len(clean) == 762

    def cv(purge):
        order = rng.permutation(1000) if not purge else np.arange(1000)
        cs = []
        for f in np.array_split(order, 5):
            tr = np.setdiff1d(np.arange(1000), f)
            if purge:
                tr = np.array([t for t in tr if t < f[0] - 19 or t > f[-1] + 19])
            pos = np.searchsorted(tr, f)
            lo = tr[np.clip(pos - 1, 0, len(tr) - 1)]
            hi = tr[np.clip(pos, 0, len(tr) - 1)]
            near = np.where(np.abs(lo - f) <= np.abs(hi - f), lo, hi)
            cs.append(np.column_stack([lab[f], lab[near]]))
        c = np.concatenate(cs)
        return np.corrcoef(c.T)[0, 1]

    assert cv(False) > 0.9
    rs = []
    for _ in range(30):
        d = rng.normal(size=1020)
        lab = np.convolve(d, np.ones(20), "valid")[:1000]
        rs.append(cv(True))
    assert abs(np.mean(rs)) < 0.25


def _lloyd(c):
    pts = np.array([[2, 0.5], [2, -0.5], [-2, 0.5], [-2, -0.5]])
    c = np.array(c, float)
    for _ in range(20):
        lab = ((pts[:, None] - c[None]) ** 2).sum(2).argmin(1)
        c = np.array([pts[lab == k].mean(0) for k in (0, 1)])
    return ((pts - c[lab]) ** 2).sum()


def test_q30():
    assert _lloyd([[0, 0.5], [0, -0.5]]) == 16
    assert _lloyd([[-2, 0], [2, 0]]) == 1
    pts = [(2, 0.5), (2, -0.5), (-2, 0.5), (-2, -0.5)]
    res = [_lloyd([pts[i], pts[j]]) for i in range(4) for j in range(i + 1, 4)]
    assert sorted(res) == [1, 1, 1, 1, 16, 16]
    assert round((1 / 3) ** 5, 4) == 0.0041


def test_q31():
    rng = np.random.default_rng(31)

    def centroid_err(x, y, tr, te):
        a = x[tr][y[tr] == 1].mean(0)
        b = x[tr][y[tr] == 0].mean(0)
        pred = ((x[te] - a) ** 2).sum(1) < ((x[te] - b) ** 2).sum(1)
        return (pred != (y[te] == 1)).mean()

    def top(x, y, m=100):
        c = np.abs(((x - x.mean(0)) * (y - y.mean())[:, None]).sum(0))
        return np.argsort(c)[-m:]

    wrong, right = [], []
    for _ in range(40):
        x = rng.normal(size=(50, 5000))
        y = rng.permutation(np.r_[np.ones(25, int), np.zeros(25, int)])
        folds = np.array_split(rng.permutation(50), 5)
        k = top(x, y)
        wrong.append(np.mean([centroid_err(x[:, k], y, np.setdiff1d(np.arange(50), f), f) for f in folds]))
        rr = []
        for f in folds:
            tr = np.setdiff1d(np.arange(50), f)
            k2 = top(x[tr], y[tr])
            rr.append(centroid_err(x[:, k2], y, tr, f))
        right.append(np.mean(rr))
    assert np.mean(wrong) < 0.05
    assert abs(np.mean(right) - 0.5) < 0.05


def test_q32():
    assert round(stats.norm.expect(lambda z: z * 100 * stats.norm.cdf(z) ** 99, lb=-10, ub=10), 2) == 2.51
    e = 2.508
    assert round(e * math.sqrt(1.25), 2) == 2.80
    assert round(0.2 * e * math.sqrt(1.25), 2) == 0.56
    s = math.sqrt(0.25 + 0.25)
    assert round(e * s, 2) == 1.77
    assert round(0.5 * e * s, 2) == 0.89
    rng = np.random.default_rng(32)
    true = rng.normal(0, 0.5, (200_000, 100))
    obs = true + rng.normal(0, 1, (200_000, 100))
    b = obs.argmax(1)
    i = np.arange(200_000)
    assert abs(obs[i, b].mean() - 2.80) < 0.01
    assert abs(true[i, b].mean() - 0.56) < 0.01


def test_q33():
    q = 1e-4

    def m(w):
        return 1 / w + q * (w + 1) * (2 * w + 1) / (6 * w)

    ws = np.arange(1, 1001)
    v = m(ws)
    best = ws[v.argmin()]
    assert abs(best - 173) <= 1
    assert round(math.sqrt(3 / q)) == 173
    assert round(m(173), 4) == 0.0116
    assert round(m(100) / m(173) - 1, 2) == 0.15
    assert round(m(300) / m(173) - 1, 2) == 0.15
    rng = np.random.default_rng(33)
    r = 20_000
    level = np.cumsum(rng.normal(0, math.sqrt(q), (r, 174)), axis=1)
    y = level[:, :173] + rng.normal(size=(r, 173))
    err = y.mean(1) - level[:, 173]
    assert abs((err**2).mean() - m(173)) < 0.0005
    # Exponential weighting at the steady-state gain.
    p = (q + math.sqrt(q * q + 4 * q)) / 2
    assert round(p, 5) == 0.01005
    assert round(p / (p + 1), 4) == 0.01
    assert round(1 - p / m(173), 2) == 0.13


def test_q34():
    assert [round(stats.norm.cdf(d / math.sqrt(2)), 3) for d in (0.1, 0.5, 1)] == [0.528, 0.638, 0.760]
    d = math.sqrt(2) * stats.norm.ppf(0.55)
    assert round(d, 3) == 0.178
    r = (d / 2) / math.sqrt(1 + d * d / 4)
    assert round(r, 3) == 0.089
    rng = np.random.default_rng(34)
    n = 2_000_000
    y = rng.integers(0, 2, n)
    s = rng.normal(size=n) + d * y
    assert abs(np.corrcoef(s, y)[0, 1] - r) < 0.002
    assert abs((rng.normal(d, 1, n) > rng.normal(0, 1, n)).mean() - 0.55) < 0.002


def test_q35():
    f = lambda p, b=0.1: b * p / (b * p + 1 - p)  # noqa: E731
    assert round(f(0.5), 3) == 0.091
    assert round(f(0.9), 3) == 0.474
    assert round(math.log(0.1), 3) == -2.303
    rng = np.random.default_rng(35)
    n = 400_000
    x = rng.normal(size=n)
    prob = 1 / (1 + np.exp(-(-3 + 1.0 * x)))
    y = rng.random(n) < prob
    keep = y | (rng.random(n) < 0.1)
    m = LogisticRegression(C=1e6).fit(x[keep, None], y[keep])
    assert abs(m.coef_[0, 0] - 1.0) < 0.05
    assert abs(m.intercept_[0] - (-3 + math.log(10))) < 0.05
    assert round(-3 + math.log(10), 2) == -0.70
    # Sampling raises the intercept by -ln(beta), and the correction takes it off. Keeping everything shifts nothing.
    assert -math.log(0.1) > 0 > math.log(0.1) and math.log(1.0) == 0
    grid = np.array([[-1.0], [0.0], [2.0]])
    corrected = f(m.predict_proba(grid)[:, 1])
    assert np.allclose(corrected, 1 / (1 + np.exp(3 - grid[:, 0])), atol=0.01)
    assert f(0.3, 1.0) == 0.3


def test_q36():
    f0 = math.log(1.5)
    assert round(f0, 3) == 0.405
    g = 30 * (0.6 - 1) + 10 * 0.6
    h = 40 * 0.24
    assert g == -6 and round(h, 1) == 9.6
    w = -g / h
    assert w == 0.625
    r = optimize.minimize_scalar(
        lambda t: 30 * math.log(1 + math.exp(-(f0 + t))) + 10 * math.log(1 + math.exp(f0 + t)),
        bounds=(0, 3),
        method="bounded",
    )
    assert abs(r.x - (math.log(3) - f0)) < 1e-4
    assert round(math.log(3) - f0, 3) == 0.693
    p = 1 / (1 + math.exp(-(f0 + 0.1 * w)))
    assert round(p, 3) == 0.615
    g2 = 30 * (0.6 - 1) + 30 * 0.6
    assert g2 == 6 and round(-g2 / (60 * 0.24), 3) == -0.417
    # The tree's overall loss falls under both steps, Newton and exact.
    assert round(0.625 / 0.693, 2) == 0.9


def test_q37():
    def gain(a, b, lam=1.0):
        gl, hl = a
        gr, hr = b
        return 0.5 * (gl**2 / (hl + lam) + gr**2 / (hr + lam) - (gl + gr) ** 2 / (hl + hr + lam))

    assert round(gain((-10, 20), (10, 20)), 2) == 4.76
    assert round(gain((-10, 1), (10, 39)), 2) == 26.25
    assert round(gain((-10, 1), (10, 39), 0), 2) == 51.28
    assert round(gain((-10, 1), (10, 39), 10), 2) == 5.57
    assert round(gain((-10, 20), (10, 20), 10), 2) == 3.33
    assert round(10 / 21, 3) == 0.476
    assert round(10 / 2, 1) == 5.0
    # Brute-force minimum of the quadratic.
    w = np.linspace(-6, 6, 120001)
    q = -10 * w + 0.5 * 2 * w * w
    assert abs(w[q.argmin()] - 5) < 1e-3
    assert abs(q.min() + 25) < 1e-3


def test_q38():
    x = np.array([0.0, 1, 2, 3, 10])
    y = np.array([0.0, 1, 2, 3, 0])
    a = np.column_stack([np.ones(5), x])
    h = np.diag(a @ np.linalg.solve(a.T @ a, a.T))
    b = np.linalg.solve(a.T @ a, a.T @ y)
    e = y - a @ b
    assert round(h[4], 4) == 0.9363
    assert round(e[4], 3) == -0.637
    assert abs(e[4] / (1 - h[4]) + 10) < 1e-9
    for i in range(5):
        m = np.delete(np.arange(5), i)
        c = np.linalg.lstsq(a[m], y[m], rcond=None)[0]
        assert abs(y[i] - a[i] @ c - e[i] / (1 - h[i])) < 1e-9
    assert round(b[1], 3) == -0.083
    assert round(h.sum(), 6) == 2


def test_q39():
    rng = np.random.default_rng(39)
    n = 50
    x = rng.normal(size=(n, 3))
    x, _ = np.linalg.qr(x)
    x = x * math.sqrt(n)
    y = rng.normal(size=n)
    b0 = x.T @ y / n
    for q in (0.5, 0.8):
        lam = (1 - q) / q * n
        sol = np.linalg.solve(x.T @ x + lam * np.eye(3), x.T @ y)
        assert np.allclose(sol, q * b0)

    # Expected dropout loss at a point, by sampling, equals the ridge formula.
    q = 0.5
    beta = np.array([1.0, -0.5, 0.2])
    d = rng.random((200_000, n, 3)) < q
    pred = (x[None] * d / q * beta).sum(2)
    emp = ((y - pred) ** 2).sum(1).mean()
    exact = ((y - x @ beta) ** 2).sum() + (1 - q) / q * (beta**2 * (x**2).sum(0)).sum()
    assert abs(emp / exact - 1) < 0.01


def test_q40():
    r = lambda v: np.maximum(v, 0)  # noqa: E731
    t = lambda v: 2 * r(v) - 4 * r(v - 0.5)  # noqa: E731
    g = (np.arange(2**14 + 1)) / 2**14
    assert np.allclose(t(g), np.where(g <= 0.5, 2 * g, 2 - 2 * g))
    v = g.copy()
    for d in range(1, 11):
        v = t(v)
        slope = np.diff(v) * 2**14
        pieces = 1 + int((np.abs(np.diff(slope)) > 1e-6).sum())
        assert pieces == 2**d
    assert 2 * 10 == 20 and 2**10 - 1 == 1023


def test_q41():
    rng = np.random.default_rng(41)
    n, p = 1000, 1000
    x = rng.normal(size=(n, p))
    x = (x - x.mean(0)) / x.std(0)
    y = rng.normal(size=n)
    y = y - y.mean()
    lam = np.abs(x.T @ y).max() / n
    assert 0.09 < lam < 0.13
    assert round(math.sqrt(2 * math.log(p) / n), 3) == 0.118
    assert round(3.43 / math.sqrt(1000), 3) == 0.108
    a = Lasso(alpha=lam * 1.001, fit_intercept=False, tol=1e-4, max_iter=2000).fit(x, y)
    assert np.count_nonzero(a.coef_) == 0
    b = Lasso(alpha=lam * 0.9, fit_intercept=False, tol=1e-4, max_iter=2000).fit(x, y)
    assert np.count_nonzero(b.coef_) > 0
    # Half the threshold lets many noise columns in.
    c = Lasso(alpha=lam * 0.5, fit_intercept=False, tol=1e-4, max_iter=2000).fit(x, y)
    assert np.count_nonzero(c.coef_) > 50


def test_q42():
    rng = np.random.default_rng(42)
    n = 1500

    def data(k):
        a = rng.normal(size=k)
        return a, (a + 0.5 * rng.normal(size=k) > 0).astype(int)

    a, y = data(n)
    at, yt = data(n)
    only = np.column_stack([a, rng.permutation(n)])
    with_copy = np.column_stack([a, a, rng.permutation(n)])
    only_t = np.column_stack([at, rng.permutation(n)])
    copy_t = np.column_stack([at, at, rng.permutation(n)])
    kw = {"n_estimators": 100, "random_state": 0, "max_features": 1, "n_jobs": 1}
    f1 = RandomForestClassifier(**kw).fit(only, y)
    f2 = RandomForestClassifier(**kw).fit(with_copy, y)
    p1 = permutation_importance(f1, only_t, yt, n_repeats=5, random_state=0).importances_mean
    p2 = permutation_importance(f2, copy_t, yt, n_repeats=5, random_state=0).importances_mean
    # Impurity: the row-id feature takes a real share.
    assert f1.feature_importances_[1] > 0.1
    # Held out, the row-id has no value.
    assert abs(p1[1]) < 0.02
    # Impurity shared among copies, and permutation on each copy falls.
    assert abs(f2.feature_importances_[0] - f2.feature_importances_[1]) < 0.1
    assert f2.feature_importances_[0] < 0.75 * f1.feature_importances_[0]
    assert p2[0] < 0.75 * p1[0]
    # Group permutation recovers the full value.
    z = copy_t.copy()
    perm = rng.permutation(n)
    z[:, 0] = z[perm, 0]
    z[:, 1] = z[perm, 1]
    assert f2.score(copy_t, yt) - f2.score(z, yt) > 0.8 * p1[0]


def test_q43():
    rng = np.random.default_rng(43)
    n = 100
    assert 1 + 50 / 49 == 1 + 50 / (n - 50 - 1)
    exact = {50: 1 + 50 / 49, 90: 1 + 90 / 9, 110: 1 + 100 / 9, 200: 1 + 100 / 99, 1000: 1 + 100 / 899}
    assert {k: round(v, 2) for k, v in exact.items()} == {50: 2.02, 90: 11.0, 110: 12.11, 200: 2.01, 1000: 1.11}
    for p in (50, 200, 1000):
        vals = []
        for _ in range(1500):
            x = rng.normal(size=(n, p))
            e = rng.normal(size=n)
            b = np.linalg.lstsq(x, e, rcond=None)[0]
            vals.append(1 + b @ b)
        assert abs(np.mean(vals) / exact[p] - 1) < 0.03
    vals = []
    for _ in range(4000):
        x = rng.normal(size=(n, 90))
        e = rng.normal(size=n)
        b = np.linalg.lstsq(x, e, rcond=None)[0]
        vals.append(1 + b @ b)
    assert abs(np.mean(vals) / exact[90] - 1) < 0.1
    # Signal follow-up: p > n adds the part of beta outside the row space, r^2 (1 - n / p).
    p, r2 = 200, 1.0
    vals = []
    for _ in range(600):
        beta = rng.normal(size=p)
        beta *= math.sqrt(r2) / np.linalg.norm(beta)
        x = rng.normal(size=(n, p))
        y = x @ beta
        b = np.linalg.lstsq(x, y, rcond=None)[0]
        vals.append(((b - beta) ** 2).sum())
    assert abs(np.mean(vals) - 0.5) < 0.02


def test_q44():
    def err(p, n=50):
        return stats.norm.cdf(-2 / math.sqrt(4 + 2 * p / n))

    assert round(err(1), 3) == 0.16
    assert round(err(100), 3) == 0.24
    assert round(err(1000), 3) == 0.382
    assert round(stats.norm.cdf(-1), 3) == 0.159
    rng = np.random.default_rng(44)
    for p, tol in ((1, 0.005), (100, 0.01), (1000, 0.01)):
        out = []
        for _ in range(300):
            a = rng.normal(size=(50, p))
            a[:, 0] += 2
            b = rng.normal(size=(50, p))
            ma, mb = a.mean(0), b.mean(0)
            w = ma - mb
            mid = (ma + mb) / 2
            t = rng.normal(size=(200, p))
            t[:, 0] += 2
            out.append((((t - mid) @ w) < 0).mean())
        assert abs(np.mean(out) - err(p)) < tol


def test_q45():
    z = 2 * math.sqrt(0.24)
    assert round(z, 4) == 0.9798
    assert math.ceil(math.log(0.01) / math.log(z)) == 226
    assert math.ceil(math.log(100) / (2 * 0.01)) == 231
    assert z <= math.exp(-2 * 0.01)
    # A real run with stumps: the bound holds at every round.
    rng = np.random.default_rng(45)
    n = 400
    x = rng.normal(size=(n, 5))
    y = np.where(x.sum(1) + 0.5 * rng.normal(size=n) > 0, 1, -1)
    w = np.ones(n) / n
    f = np.zeros(n)
    bound = 1.0
    for _ in range(60):
        best = None
        for j in range(5):
            for t in np.quantile(x[:, j], np.linspace(0.05, 0.95, 19)):
                for s in (1, -1):
                    pred = s * np.where(x[:, j] > t, 1, -1)
                    e = w[pred != y].sum()
                    if best is None or e < best[0]:
                        best = (e, pred)
        e, pred = best
        a = 0.5 * math.log((1 - e) / e)
        f += a * pred
        w = w * np.exp(-a * y * pred)
        zt = w.sum()
        assert abs(zt - 2 * math.sqrt(e * (1 - e))) < 1e-9
        w /= zt
        bound *= zt
        assert (np.sign(f) != y).mean() <= bound + 1e-12
        assert abs(np.exp(-y * f).mean() - bound) < 1e-9


def test_follow_ups():
    # 2: test set that keeps the best of 20 null models below 52%.
    assert round((1.867 * 50 / 2) ** 2, -1) == 2180
    # 6: nested search.
    assert 5 * 5000 == 25000
    # 11: ten more useless parameters.
    assert 2 * 10 / 100 == 0.2
    # 14: within 1% of the limit.
    assert math.ceil(0.7 / 0.003) == 234
    # 19: smaller penalty.
    b = optimize.brentq(lambda t: 2 / (1 + math.exp(t)) - 0.01 * t, 0.1, 20)
    assert round(b, 2) == 3.91
    assert round(1 / (1 + math.exp(-b)), 2) == 0.98
    # 20: logistic regression shares the coefficient among copies.
    rng = np.random.default_rng(120)
    x = rng.normal(size=(5000, 1))
    y = rng.random(5000) < 1 / (1 + np.exp(-x[:, 0]))
    one = LogisticRegression(C=1e6).fit(x, y).coef_[0]
    three = LogisticRegression(C=1e6).fit(np.column_stack([x, x, x]), y).coef_[0]
    assert abs(three.sum() - one[0]) < 1e-2 and abs(three[0] - three[1]) < 1e-2
    # 24: right side.
    p = 1 / (1 + math.exp(-7.0))
    assert round(p - 1, 5) == -0.00091
    assert (p - 1) * p * (1 - p) > -1e-3
    assert round(((p - 1) * p * (1 - p)) * 1e7, 1) == -8.3
    # 25: rank-only, so a monotone map leaves it alone.
    pos, neg = np.array([0.9, 0.6, 0.4]), np.array([0.7, 0.3, 0.2, 0.1])
    assert (np.exp(pos)[:, None] > np.exp(neg)).sum() == 10
    # 26: trade cost.
    assert round(1.1 / 1.5, 3) == 0.733
    # 27: winners smaller than losers.
    assert round(1 / 1.9, 3) == 0.526
    # 28: embargo.
    assert 762 - 5 == 757
    # 30: seeded start.
    assert round(1 / 34, 3) == 0.029
    # 32: a lower prior mean.
    assert round(-0.2 + 0.2 * 2.80, 2) == 0.36
    # 33: half-life.
    assert round(math.log(2) / 0.01) == 69
    # 34: hit rate at the midpoint threshold.
    assert round(stats.norm.cdf(0.178 / 2), 3) == 0.535
    # 36: other leaf.
    assert round(-math.log(1.5), 3) == -0.405
    # 38: replacing the leverage with its mean.
    assert round(-0.637 / (1 - 2 / 5), 2) == -1.06
    # 40
    assert 2**30 - 1 == 1_073_741_823
    # 41: the size of the largest noise statistic.
    assert round(math.sqrt(2 * math.log(1000)), 2) == 3.72
    # 44: when does error reach 30%?
    t = 2 / stats.norm.ppf(0.7)
    assert round((t**2 - 4) * 25) == 264
    # 45: tiny check of the elementary bound.
    assert math.sqrt(1 - 4 * 0.01) <= math.exp(-2 * 0.01)


def test_max_abs_normal():
    rng = np.random.default_rng(141)
    assert abs(np.abs(rng.standard_normal((20000, 1000))).max(axis=1).mean() - 3.43) < 0.01


def test_more_printed():
    # 41: envelope growth to one million features, and the size of a weak feature's contribution.
    assert round(math.sqrt(2 * math.log(1e6)), 2) == 5.26
    assert round(5.26 / 3.72 - 1, 1) == 0.4
    # 45: rounds to reach below 1 / n.
    assert math.ceil(math.log(1 / 400) / math.log(2 * math.sqrt(0.24))) == 294
    # 34: the phi inverse quoted.
    assert round(stats.norm.ppf(0.55), 4) == 0.1257
    # 22: the bound.
    assert abs(0.25**10 - 9.54e-07) < 1e-8
