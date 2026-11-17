#!/usr/bin/env python3
"""selftest.py - end-to-end check on synthetic data with a KNOWN truth (standard library only).

Plants: 20 groups x 5 years, true prevalence per cell, a classifier with known error (Beta scores),
three simulated coders (95% accurate each), and an outcome driven by prevalence with a planted coefficient.
Checks: (1) correct.py recovers the true prevalence within its interval, and beats the raw rate;
        (2) panel.py recovers the sign of the planted coefficient, and raw-vs-corrected is shown.
Usage:  python3 scripts/selftest.py [--keep DIR]      (runs in a temporary directory by default)
"""
import argparse, csv, os, random, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(*args, cwd):
    r = subprocess.run([PY, os.path.join(HERE, args[0]), *args[1:]], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("FAILED: %s\n%s%s" % (args, r.stdout, r.stderr))
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", help="write the synthetic files here and keep them")
    ap.add_argument("--beta", type=float, default=-2.0, help="planted effect of prevalence on the outcome change")
    a = ap.parse_args()
    d = a.keep or tempfile.mkdtemp(prefix="vcalibrate_")
    os.makedirs(d, exist_ok=True)
    rng = random.Random(42)
    G, YEARS, N = 20, [2010, 2011, 2012, 2013, 2014], 400
    truth, scored, labels = {}, [], {}
    for g in range(G):
        base = rng.uniform(0.08, 0.35)
        for y in YEARS:
            p = min(0.9, max(0.02, base + rng.gauss(0, 0.07)))
            truth_cell = 0
            for i in range(N):
                lab = 1 if rng.random() < p else 0
                score = rng.betavariate(4, 2) if lab else rng.betavariate(2, 4)
                iid = "g%02d_%d_%d" % (g, y, i)
                scored.append([iid, "g%02d" % g, y, "%.5f" % score])
                labels[iid] = lab
                truth_cell += lab
            truth[("g%02d" % g, str(y))] = truth_cell / N
    with open(os.path.join(d, "scored.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "group", "year", "score"]); w.writerows(scored)
    out = run("sample.py", "scored.csv", "--by", "group,year", "--n", "60", "--bins", "5", "--seed", "7", cwd=d)
    print(out.strip())
    # simulated blind coders: each 95% accurate, independent
    with open(os.path.join(d, "coding_sheet.csv"), newline="") as f:
        sheet = list(csv.DictReader(f))
    with open(os.path.join(d, "coded.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "coder_1", "coder_2", "coder_3"])
        for r in sheet:
            lab = labels[r["id"]]
            w.writerow([r["id"]] + [lab if rng.random() < 0.95 else 1 - lab for _ in range(3)])
    print(run("reference.py", "coded.csv", cwd=d).strip())
    print(run("correct.py", "--scored", "scored.csv", "--sample", "sample.csv", "--reference", "reference.csv",
              "--by", "group,year", "--error-by", "group", "--boot", "300", "--seed", "3", "--out", "corrected.csv", cwd=d)
          .strip().splitlines()[0])
    rows = list(csv.DictReader(open(os.path.join(d, "corrected.csv"))))
    cover, err_c, err_r, n = 0, 0.0, 0.0, 0
    for r in rows:
        t = truth[(r["group"], r["year"])]
        cover += float(r["lo"]) <= t <= float(r["hi"])
        err_c += abs(float(r["corrected"]) - t); err_r += abs(float(r["raw_rate"]) - t); n += 1
    mean_bias_c = sum(float(r["corrected"]) - truth[(r["group"], r["year"])] for r in rows) / n
    mean_bias_r = sum(float(r["raw_rate"]) - truth[(r["group"], r["year"])] for r in rows) / n
    print("\nCORRECTION  cells=%d  interval covers truth: %.0f%%  mean abs error corrected %.3f vs raw %.3f  "
          "mean bias corrected %+.3f vs raw %+.3f" % (n, 100 * cover / n, err_c / n, err_r / n, mean_bias_c, mean_bias_r))
    ok1 = cover / n >= 0.90 and err_c < err_r and abs(mean_bias_c) < 0.01
    # outcome: change over one period = beta * TRUE prevalence + noise
    yv = {}
    for g in range(G):
        lvl = rng.uniform(0.3, 0.7)
        for y in YEARS:
            yv[("g%02d" % g, y)] = lvl
            if y != YEARS[-1]:
                lvl += a.beta * truth[("g%02d" % g, str(y))] * 0.1 + rng.gauss(0, 0.01)
    with open(os.path.join(d, "outcome.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["group", "year", "value"])
        for (g, y), v in sorted(yv.items()):
            w.writerow([g, y, "%.5f" % v])
    for col in ("corrected", "raw_rate"):
        print("\n" + run("panel.py", "--rates", "corrected.csv", "--outcome", "outcome.csv", "--x", col,
                         "--lags", "1,2", "--boot", "499", cwd=d).strip())
    # planted coefficient is beta*0.1 per period: sign must match
    res = run("panel.py", "--rates", "corrected.csv", "--outcome", "outcome.csv", "--lags", "1", "--out", "panel.csv", cwd=d)
    b1 = float(list(csv.DictReader(open(os.path.join(d, "panel.csv"))))[0]["beta"])
    ok2 = (b1 < 0) == (a.beta < 0)
    print("\nPLANTED effect per period: %+.2f   estimated (corrected, lag 1): %+.3f" % (a.beta * 0.1, b1))
    print("RESULT  correction recovers truth: %s   panel recovers sign: %s" % ("PASS" if ok1 else "FAIL", "PASS" if ok2 else "FAIL"))
    if not a.keep:
        print("(temporary files in %s)" % d)
    sys.exit(0 if ok1 and ok2 else 1)


if __name__ == "__main__":
    main()
