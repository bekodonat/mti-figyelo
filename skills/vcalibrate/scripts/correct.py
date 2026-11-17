#!/usr/bin/env python3
"""correct.py - correct each cell's classifier-based rate for classifier error (standard library only, Python 3.9+).

Rogan-Gladen:  corrected = (raw + specificity - 1) / (sensitivity + specificity - 1), clipped to [0, 1].
  raw          share of the cell's FULL corpus with score >= threshold (observed in full; its binomial noise still enters the interval)
  sensitivity  design-weighted share of reference-positive sample items the classifier calls positive
  specificity  design-weighted share of reference-negative sample items the classifier calls negative
Weights = inverse inclusion probability per score stratum (the sample is score-stratified, so unweighted
sensitivity and specificity would be biased). Interval: bootstrap that resamples the sample WITHIN strata,
recomputes sensitivity and specificity, AND redraws the cell's raw rate (binomial noise: even with known error
rates, how many of THIS cell's texts the classifier gets wrong is itself random), then re-applies the correction.
Without the second part the interval covers only the calibration uncertainty and runs too narrow (86% coverage
of a nominal 95% in the self-test; ~95% with it). --census-only switches the redraw off. Reproducible with --seed.

Inputs : --scored  full scored CSV    id, <by...>, score
         --sample  sample.csv         from sample.py (id, stratum, n_stratum ...)
         --reference reference.csv    from reference.py (id, reference)
Output : --out corrected.csv  <by...>, n_corpus, n_pos_pred, raw_rate, n_ref, sens, spec, weighted_prev,
                              corrected, lo, hi, flag
--error-by pools sensitivity and specificity over a coarser unit than the cell (e.g. cells = country-year,
error unit = country) when 300 items per cell is too few to estimate error rates cell by cell.
"""
import argparse, csv, random, sys
from collections import defaultdict


def quantile(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def clip(x):
    return max(0.0, min(1.0, x))


def rg(raw, sens, spec):
    if sens is None or spec is None:
        return None
    j = sens + spec - 1
    if j <= 1e-9:
        return None
    return clip((raw + spec - 1) / j)


def draw_rate(rng, n, p):
    """Binomial(n, p)/n: exact for small n, normal approximation for large n (standard library only)."""
    if n <= 200:
        return sum(rng.random() < p for _ in range(n)) / n
    return clip(p + rng.gauss(0.0, (p * (1 - p) / n) ** 0.5))


def sens_spec(sums):
    """sums = [w*ref*pred, w*ref, w*(1-ref)*(1-pred), w*(1-ref)]"""
    a, b, c, d = sums
    return (a / b if b > 0 else None), (c / d if d > 0 else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scored", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--threshold", type=float, default=0.5, help="score >= threshold counts as positive (default 0.5)")
    ap.add_argument("--by", default="group")
    ap.add_argument("--error-by", help="subset of --by used to pool sensitivity/specificity (default: same as --by)")
    ap.add_argument("--boot", type=int, default=500, help="bootstrap replicates (default 500)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--census-only", action="store_true",
                    help="treat the raw rate as fixed (calibration uncertainty only; intervals run narrow)")
    ap.add_argument("--min-j", type=float, default=0.3, help="warn when sens+spec-1 is below this (default 0.3)")
    ap.add_argument("--id-col", default="id")
    ap.add_argument("--score-col", default="score")
    ap.add_argument("--out", default="corrected.csv")
    a = ap.parse_args()

    by = [c.strip() for c in a.by.split(",")]
    eby = [c.strip() for c in a.error_by.split(",")] if a.error_by else by
    if not set(eby) <= set(by):
        sys.exit("--error-by must be a subset of --by")

    # full corpus: census per cell
    n_corpus, n_pos = defaultdict(int), defaultdict(int)
    with open(a.scored, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cell = tuple(r[c] for c in by)
            n_corpus[cell] += 1
            n_pos[cell] += float(r[a.score_col]) >= a.threshold

    ref = {}
    with open(a.reference, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["reference"] in ("0", "1"):
                ref[r[a.id_col]] = int(r["reference"])

    # sample rows with a usable reference; recompute weights over the retained items
    kept, dropped = [], 0
    with open(a.sample, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r[a.id_col] in ref:
                kept.append(r)
            else:
                dropped += 1
    if dropped:
        print("note: %d sampled items have no reference (ties or incomplete) and were dropped; weights recomputed" % dropped)
    strata = defaultdict(list)            # (cell, bin) -> [(ref, pred)]
    nh = {}
    for r in kept:
        cell = tuple(r[c] for c in by)
        key = (cell, r["stratum"])
        strata[key].append((ref[r[a.id_col]], int(float(r[a.score_col]) >= a.threshold)))
        nh[key] = int(r["n_stratum"])
    weight = {k: nh[k] / len(v) for k, v in strata.items()}

    def unit_of(cell):
        return tuple(cell[by.index(c)] for c in eby)

    def unit_sums(resample, rng):
        sums = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        cells = defaultdict(lambda: [0.0, 0.0])    # weighted ref-positive mass, total mass per cell
        for key in sorted(strata):
            items = strata[key]
            if resample:
                items = [items[rng.randrange(len(items))] for _ in items]
            w = weight[key]
            s = sums[unit_of(key[0])]
            c = cells[key[0]]
            for (y, p) in items:
                s[0] += w * y * p
                s[1] += w * y
                s[2] += w * (1 - y) * (1 - p)
                s[3] += w * (1 - y)
                c[0] += w * y
                c[1] += w
        return sums, cells

    sums0, cells0 = unit_sums(False, None)
    rng = random.Random(a.seed)
    allcells = sorted(n_corpus)
    boots = defaultdict(list)
    for _ in range(a.boot):
        sb, _c = unit_sums(True, rng)
        sbe = {u: sens_spec(s) for u, s in sb.items()}
        for cell in allcells:
            u = unit_of(cell)
            if u in sbe:
                raw = n_pos[cell] / n_corpus[cell]
                if not a.census_only:
                    raw = draw_rate(rng, n_corpus[cell], raw)
                v = rg(raw, *sbe[u])
                if v is not None:
                    boots[cell].append(v)

    weak = 0
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([*by, "n_corpus", "n_pos_pred", "raw_rate", "n_ref", "sens", "spec", "weighted_prev",
                    "corrected", "lo", "hi", "flag"])
        for cell in allcells:
            u = unit_of(cell)
            raw = n_pos[cell] / n_corpus[cell]
            se, sp = sens_spec(sums0[u]) if u in sums0 else (None, None)
            nref = sum(len(v) for k, v in strata.items() if k[0] == cell)
            wp = cells0[cell][0] / cells0[cell][1] if cell in cells0 and cells0[cell][1] > 0 else None
            est = rg(raw, se, sp)
            flag = []
            if est is None:
                flag.append("no_estimate(sens/spec undefined or sens+spec<=1)")
            elif se + sp - 1 < a.min_j:
                flag.append("weak_classifier(J=%.2f)" % (se + sp - 1)); weak += 1
            b = sorted(boots[cell])
            fmt = lambda x: "" if x is None else "%.5f" % x
            w.writerow([*cell, n_corpus[cell], n_pos[cell], "%.5f" % raw, nref, fmt(se), fmt(sp), fmt(wp), fmt(est),
                        fmt(quantile(b, 0.025)) if b else "", fmt(quantile(b, 0.975)) if b else "", ";".join(flag)])
    print("cells: %d   error units: %d   bootstrap replicates: %d   seed: %d" % (len(allcells), len(sums0), a.boot, a.seed))
    for u in sorted(sums0):
        se, sp = sens_spec(sums0[u])
        if se is not None and sp is not None:
            print("  unit %-20s sensitivity %.3f  specificity %.3f  (Youden J %.3f)" % ("|".join(u), se, sp, se + sp - 1))
    if weak:
        print("warning: %d cell(s) have sens+spec-1 < %.2f: the correction divides by it and blows up noise" % (weak, a.min_j))
    print("wrote %s (report raw_rate AND corrected, never raw alone)" % a.out)


if __name__ == "__main__":
    main()
