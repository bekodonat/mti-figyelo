#!/usr/bin/env python3
"""panel.py - dependency-free reference panel regression (standard library only, Python 3.9+).

Model, for each lag L:   y[t+L] - y[t] = beta * x[t] + (optional) gamma * y[t] + unit fixed effect + error
  x = corrected prevalence (or raw, for comparison) of a group-year, y = an outcome such as an index.
Estimation: OLS after subtracting each unit's mean (unit fixed effects). Reports the coefficient, a
cluster-robust standard error (clusters = units), and a WILD CLUSTER BOOTSTRAP p-value (Rademacher weights,
null imposed), which behaves better than the asymptotic p with few clusters.

Inputs : --rates   corrected.csv    columns: unit, time, x            (e.g. group, year, corrected)
         --outcome outcome.csv      columns: unit, time, y            (e.g. group, year, value)
Time must be an integer in the same unit as --lags (years for annual data: lag 1 = 12 months, 2 = 24).
For real projects use R (fixest, plm, fwildclusterboot) or Python statsmodels; this file is a small,
auditable reference so the workflow runs anywhere with no installs.
"""
import argparse, csv, random, sys
from collections import defaultdict


def solve(A, B):
    """Solve A X = B by Gauss-Jordan (A k x k, B k x m); returns X."""
    k = len(A)
    M = [A[i][:] + B[i][:] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            raise ValueError("singular matrix (collinear regressors?)")
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        M[c] = [v / pv for v in M[c]]
        for r in range(k):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [vr - f * vc for vr, vc in zip(M[r], M[c])]
    return [row[k:] for row in M]


def xtx(X):
    k = len(X[0])
    return [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]


def ols(X, y, XtXinv=None):
    k = len(X[0])
    if XtXinv is None:
        XtXinv = solve(xtx(X), [[1.0 if i == j else 0.0 for j in range(k)] for i in range(k)])
    Xty = [sum(r[i] * v for r, v in zip(X, y)) for i in range(k)]
    return [sum(XtXinv[i][j] * Xty[j] for j in range(k)) for i in range(k)], XtXinv


def cluster_se(X, e, g, XtXinv, idx, n, G):
    k = len(X[0])
    s = defaultdict(lambda: [0.0] * k)
    for r, ei, gi in zip(X, e, g):
        for j in range(k):
            s[gi][j] += r[j] * ei
    meat = [[0.0] * k for _ in range(k)]
    for v in s.values():
        for i in range(k):
            for j in range(k):
                meat[i][j] += v[i] * v[j]
    # V = XtXinv * meat * XtXinv, only the (idx, idx) element is needed
    row = [sum(XtXinv[idx][i] * meat[i][j] for i in range(k)) for j in range(k)]
    var = sum(row[j] * XtXinv[j][idx] for j in range(k))
    return (max(var, 0.0) * G / (G - 1)) ** 0.5 if G > 1 else float("nan")


def demean(vals, groups):
    tot, cnt = defaultdict(float), defaultdict(int)
    for v, g in zip(vals, groups):
        tot[g] += v
        cnt[g] += 1
    return [v - tot[g] / cnt[g] for v, g in zip(vals, groups)]


def read_xy(path, unit, time, col):
    d = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r[col] not in ("", None):
                d[(r[unit], int(r[time]))] = float(r[col])
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rates", required=True)
    ap.add_argument("--outcome", required=True)
    ap.add_argument("--x", default="corrected", help="column in --rates (default corrected; use raw_rate to compare)")
    ap.add_argument("--y", default="value", help="column in --outcome (default value)")
    ap.add_argument("--unit", default="group")
    ap.add_argument("--time", default="year")
    ap.add_argument("--lags", default="1,2", help="comma-separated lags in time units (default 1,2)")
    ap.add_argument("--baseline", action="store_true", help="also control for the outcome level at t")
    ap.add_argument("--boot", type=int, default=999)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", help="optional CSV of the results")
    a = ap.parse_args()

    xs = read_xy(a.rates, a.unit, a.time, a.x)
    ys = read_xy(a.outcome, a.unit, a.time, a.y)
    results = []
    for L in [int(v) for v in a.lags.split(",")]:
        rows = []
        for (u, t), x in sorted(xs.items()):
            if (u, t) in ys and (u, t + L) in ys:
                rows.append((u, t, x, ys[(u, t)], ys[(u, t + L)] - ys[(u, t)]))
        units = sorted({r[0] for r in rows})
        cnt = defaultdict(int)
        for r in rows:
            cnt[r[0]] += 1
        rows = [r for r in rows if cnt[r[0]] >= 2]         # a unit with one row has no within variation
        g = [r[0] for r in rows]
        G = len(set(g))
        n = len(rows)
        cols = [[r[2] for r in rows]] + ([[r[3] for r in rows]] if a.baseline else [])
        dm = [demean(c, g) for c in cols]
        X = [list(t) for t in zip(*dm)]
        y = demean([r[4] for r in rows], g)
        k = len(X[0]) if n else 0
        if n <= k + G or G < 3:
            print("lag %d: too few observations (N=%d, units=%d)" % (L, n, G))
            continue
        b, inv = ols(X, y)
        e = [yi - sum(bj * xj for bj, xj in zip(b, xr)) for xr, yi in zip(X, y)]
        se = cluster_se(X, e, g, inv, 0, n, G)
        tstat = b[0] / se if se > 0 else float("nan")
        ssr = sum(v * v for v in e)
        sst = sum(v * v for v in y)
        # wild cluster bootstrap, null imposed: restricted fit = controls only
        if a.baseline:
            Xr = [[r[1]] for r in X]
            br, invr = ols(Xr, y)
            fit0 = [br[0] * r[0] for r in Xr]
        else:
            fit0 = [0.0] * n
        e0 = [yi - f for yi, f in zip(y, fit0)]
        rng = random.Random(a.seed + L)
        names = sorted(set(g))
        ge = 0
        done = 0
        for _ in range(a.boot):
            w = {u: rng.choice((-1.0, 1.0)) for u in names}
            ystar = [f + w[gi] * ei for f, gi, ei in zip(fit0, g, e0)]
            bs, _ = ols(X, ystar, inv)
            es = [yi - sum(bj * xj for bj, xj in zip(bs, xr)) for xr, yi in zip(X, ystar)]
            ses = cluster_se(X, es, g, inv, 0, n, G)
            if ses > 0:
                done += 1
                ge += abs(bs[0] / ses) >= abs(tstat) - 1e-12
        p = (ge + 1) / (done + 1) if done else float("nan")
        results.append((L, b[0], se, tstat, p, n, G, 1 - ssr / sst if sst > 0 else float("nan")))
    print("x = %s (%s)   outcome = %s   unit fixed effects%s" % (a.x, a.rates, a.y, " + baseline outcome" if a.baseline else ""))
    print("%-5s %10s %10s %8s %12s %5s %6s %9s" % ("lag", "beta", "cl.SE", "t", "wild-boot p", "N", "units", "within R2"))
    for L, bb, se, ts, p, n, G, r2 in results:
        print("%-5d %10.4f %10.4f %8.2f %12.3f %5d %6d %9.3f" % (L, bb, se, ts, p, n, G, r2))
    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["lag", "beta", "cluster_se", "t", "wild_boot_p", "n", "units", "within_r2"])
            w.writerows(results)


if __name__ == "__main__":
    main()
