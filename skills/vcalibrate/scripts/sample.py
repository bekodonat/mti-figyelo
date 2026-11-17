#!/usr/bin/env python3
"""sample.py - draw a score-stratified sample for blind coding (standard library only, Python 3.9+).

Input : scored CSV with columns  id, <by columns, default: group>, score   (score in 0..1; extra columns, e.g. text, are allowed)
Output: sample.csv        id, <by>, score, stratum, n_stratum, n_sampled, weight
        coding_sheet.csv  id, [text], coder_1..coder_k (blank)  -- NO scores, shuffled, for the coders

Within every cell (one value of the --by columns) the corpus is cut into score bins (strata). N items are
allocated equally over the bins (capped by bin size, leftovers redistributed), drawn without replacement.
weight = n_stratum / n_sampled = inverse inclusion probability, used later by correct.py.
Reproducible: cells, bins and ids are visited in sorted order, and the draw uses random.Random(seed).
"""
import argparse, csv, random, sys
from collections import defaultdict


def bin_of(score, edges):
    for i in range(len(edges) - 2):
        if score < edges[i + 1]:
            return i
    return len(edges) - 2


def allocate(sizes, n):
    """Equal allocation over non-empty bins, capped by size, leftover spread round-robin."""
    bins = sorted(b for b, s in sizes.items() if s > 0)
    alloc = {b: 0 for b in bins}
    left = min(n, sum(sizes[b] for b in bins))
    while left > 0:
        open_bins = [b for b in bins if alloc[b] < sizes[b]]
        if not open_bins:
            break
        share = max(1, left // len(open_bins))
        for b in open_bins:
            take = min(share, sizes[b] - alloc[b], left)
            alloc[b] += take
            left -= take
            if left == 0:
                break
    return alloc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scored")
    ap.add_argument("--by", default="group", help="comma-separated columns defining a cell (default: group)")
    ap.add_argument("--n", type=int, default=300, help="items to code per cell (default 300)")
    ap.add_argument("--bins", type=int, default=5, help="equal-width score bins on 0..1 (default 5)")
    ap.add_argument("--edges", help="explicit bin edges, e.g. 0,0.1,0.3,0.6,0.9,1.0000001 (overrides --bins)")
    ap.add_argument("--id-col", default="id")
    ap.add_argument("--score-col", default="score")
    ap.add_argument("--text-col", help="copy this column into the coding sheet (optional)")
    ap.add_argument("--coders", type=int, default=3, help="blank coder columns in the coding sheet (default 3)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="sample.csv")
    ap.add_argument("--sheet", default="coding_sheet.csv")
    a = ap.parse_args()

    by = [c.strip() for c in a.by.split(",")]
    edges = [float(x) for x in a.edges.split(",")] if a.edges else \
        [i / a.bins for i in range(a.bins)] + [1.0 + 1e-9]
    cells = defaultdict(lambda: defaultdict(list))   # cell -> bin -> [(id, score, text)]
    seen = set()
    with open(a.scored, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            i = r[a.id_col]
            if i in seen:
                sys.exit("duplicate id in scored file: " + i)
            seen.add(i)
            s = float(r[a.score_col])
            if not 0 <= s <= 1:
                sys.exit("score outside 0..1 for id " + i)
            cells[tuple(r[c] for c in by)][bin_of(s, edges)].append((i, s, r.get(a.text_col, "") if a.text_col else ""))

    rng = random.Random(a.seed)
    rows, sheet = [], []
    for cell in sorted(cells):
        strata = cells[cell]
        alloc = allocate({b: len(v) for b, v in strata.items()}, a.n)
        for b in sorted(alloc):
            if alloc[b] == 0:
                continue
            pool = sorted(strata[b])
            for (i, s, t) in rng.sample(pool, alloc[b]):
                rows.append([i, *cell, "%.6f" % s, b, len(pool), alloc[b], "%.6f" % (len(pool) / alloc[b])])
                sheet.append([i, t] if a.text_col else [i])
    order = list(range(len(sheet)))
    rng.shuffle(order)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", *by, "score", "stratum", "n_stratum", "n_sampled", "weight"])
        w.writerows(rows)
    with open(a.sheet, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id"] + (["text"] if a.text_col else []) + ["coder_%d" % (k + 1) for k in range(a.coders)])
        for k in order:
            w.writerow(sheet[k] + [""] * a.coders)
    print("cells: %d   corpus items: %d   sampled: %d" % (len(cells), len(seen), len(rows)))
    short = [c for c in sorted(cells) if sum(len(v) for v in cells[c].values()) < a.n]
    if short:
        print("note: %d cell(s) smaller than --n were taken whole (weight 1)" % len(short))
    print("wrote %s and %s (give coders only the sheet, never the scores)" % (a.out, a.sheet))


if __name__ == "__main__":
    main()
