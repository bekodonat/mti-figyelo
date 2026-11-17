#!/usr/bin/env python3
"""agreement.py — hand codes against machine labels, matched by an id column.

Usage:
  python3 agreement.py hand.csv labels.csv [--id file] [--code code] [--mismatches mismatches.csv]
  python3 agreement.py codings.csv --coders human,model              # one file, two coder columns
  python3 agreement.py --selftest

Prints: matched n, exact agreement, Cohen's kappa, per-category n / base rate / precision / recall / F1
(the first file or coder is the reference), the confusion matrix and the mismatches. Standard library only.
"""
import sys, csv, argparse
from collections import Counter, defaultdict

def read(path, idc, codec):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if rows and (idc not in rows[0] or codec not in rows[0]):
        sys.exit(f"{path}: needs columns {idc!r} and {codec!r}; has {list(rows[0])}")
    out = {}
    for r in rows:
        k = (r[idc] or "").strip(); v = (r[codec] or "").strip()
        if k and v: out[k] = v
    return out

def kappa(pairs):
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[c] / n * cb[c] / n for c in set(ca) | set(cb))
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")

def report(pairs, ids=None):
    po, k = kappa(pairs); n = len(pairs)
    cats = sorted(set(a for a, _ in pairs) | set(b for _, b in pairs))
    print(f"matched units: {n} · exact agreement: {po:.3f} · Cohen's kappa: {k:.3f}")
    print("\nper category (reference = first file / first coder):")
    print(f"{'code':<16}{'n_ref':>6}{'base':>7}{'prec':>7}{'rec':>6}{'F1':>6}")
    for c in cats:
        tp = sum(1 for a, b in pairs if a == c and b == c); fn = sum(1 for a, b in pairs if a == c and b != c)
        fp = sum(1 for a, b in pairs if a != c and b == c); nref = tp + fn
        prec = tp / (tp + fp) if tp + fp else float("nan"); rec = tp / nref if nref else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if prec + rec and prec == prec and rec == rec else float("nan")
        flag = "  (n < 10: no verdict)" if nref < 10 else ""
        print(f"{c:<16}{nref:>6}{nref / n:>7.2f}{prec:>7.2f}{rec:>6.2f}{f1:>6.2f}{flag}")
    print("\nconfusion matrix (rows = reference, columns = compared):")
    w = max(6, max(len(c) for c in cats) + 1); m = defaultdict(Counter)
    for a, b in pairs: m[a][b] += 1
    print(" " * w + "".join(f"{c:>{w}}" for c in cats))
    for a in cats: print(f"{a:<{w}}" + "".join(f"{m[a][b]:>{w}}" for b in cats))
    mism = [(i, a, b) for i, (a, b) in zip(ids or range(n), pairs) if a != b]
    print(f"\nmismatches: {len(mism)}")
    for i, a, b in mism: print(f"  {i}: reference {a} · compared {b}")
    return mism

def selftest():
    pairs = [("x", "x")] * 20 + [("y", "y")] * 15 + [("x", "y")] * 5 + [("y", "x")] * 10
    po, k = kappa(pairs); assert abs(po - 0.70) < 1e-9 and abs(k - 0.40) < 1e-9, (po, k)
    print("selftest ok: exact 0.70, kappa 0.40 on the textbook 50-unit table")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*"); ap.add_argument("--id", default="file"); ap.add_argument("--code", default="code")
    ap.add_argument("--coders", default=""); ap.add_argument("--mismatches", default=""); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); return
    if a.coders:
        c1, c2 = [c.strip() for c in a.coders.split(",")][:2]
        with open(a.files[0], newline="", encoding="utf-8") as fh: rows = list(csv.DictReader(fh))
        ids = [r.get(a.id, str(i)) for i, r in enumerate(rows) if (r.get(c1) or "").strip() and (r.get(c2) or "").strip()]
        pairs = [((r[c1] or "").strip(), (r[c2] or "").strip()) for r in rows if (r.get(c1) or "").strip() and (r.get(c2) or "").strip()]
    else:
        if len(a.files) != 2: ap.error("give hand.csv and labels.csv, or one file with --coders A,B")
        h, m = read(a.files[0], a.id, a.code), read(a.files[1], a.id, a.code)
        ids = sorted(set(h) & set(m)); pairs = [(h[i], m[i]) for i in ids]
        print(f"hand rows: {len(h)} · machine rows: {len(m)} · matched by {a.id!r}: {len(ids)}")
    if not pairs: sys.exit("no matched units")
    mism = report(pairs, ids)
    if a.mismatches:
        with open(a.mismatches, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow([a.id, "reference", "compared", "verdict"]); [w.writerow([i, x, y, ""]) for i, x, y in mism]
        print("written:", a.mismatches)

if __name__ == "__main__": main()
