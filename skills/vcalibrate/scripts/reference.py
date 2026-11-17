#!/usr/bin/env python3
"""reference.py - majority-vote reference labels from k blind coders (standard library only, Python 3.9+).

Input : coded CSV with  id  plus one 0/1 column per coder (default: every column named coder_*)
        accepted values: 0/1, yes/no, true/false (any case); a blank cell means "not coded"
Output: reference.csv  id, reference, votes_pos, k, tie
Prints: label counts, pairwise percent agreement, Fleiss' kappa, ties, incomplete rows.
A tie (even k, votes split evenly) gets an empty reference and is dropped later, unless --tie says otherwise.
"""
import argparse, csv, itertools, sys

YES = {"1", "yes", "y", "true", "t", "1.0"}
NO = {"0", "no", "n", "false", "f", "0.0"}


def val(x):
    x = (x or "").strip().lower()
    if x == "":
        return None
    if x in YES:
        return 1
    if x in NO:
        return 0
    sys.exit("cannot read label %r (use 0/1, yes/no, true/false or blank)" % x)


def fleiss(rows, k):
    n = len(rows)
    if n == 0 or k < 2:
        return float("nan")
    pbar = sum((v * v + (k - v) ** 2 - k) / (k * (k - 1)) for v in rows) / n
    p1 = sum(rows) / (n * k)
    pe = p1 * p1 + (1 - p1) ** 2
    return float("nan") if pe == 1 else (pbar - pe) / (1 - pe)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("coded")
    ap.add_argument("--coders", help="comma-separated coder columns (default: all coder_* columns)")
    ap.add_argument("--id-col", default="id")
    ap.add_argument("--tie", choices=["drop", "positive", "negative"], default="drop")
    ap.add_argument("--identity-flag", type=float, default=0.90,
                    help="warn when two coders agree on at least this share (default 0.90)")
    ap.add_argument("--out", default="reference.csv")
    a = ap.parse_args()

    with open(a.coded, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        cols = [c.strip() for c in a.coders.split(",")] if a.coders else [c for c in rd.fieldnames if c.startswith("coder_")]
        if len(cols) < 3:
            print("warning: fewer than three coder columns; majority needs an odd k >= 3 to avoid ties")
        recs = [(r[a.id_col], [val(r[c]) for c in cols]) for r in rd]
    k = len(cols)
    full = [(i, v) for i, v in recs if None not in v]
    print("coders: %s" % ", ".join(cols))
    print("rows: %d   fully coded: %d   incomplete (dropped): %d" % (len(recs), len(full), len(recs) - len(full)))

    out, ties, votes = [], 0, []
    for i, v in full:
        pos = sum(v)
        votes.append(pos)
        tie = (2 * pos == k)
        ties += tie
        if tie:
            ref = {"drop": "", "positive": 1, "negative": 0}[a.tie]
        else:
            ref = 1 if 2 * pos > k else 0
        out.append([i, ref, pos, k, int(tie)])
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "reference", "votes_pos", "k", "tie"])
        w.writerows(out)
    npos = sum(1 for o in out if o[1] == 1)
    nneg = sum(1 for o in out if o[1] == 0)
    print("reference: %d positive, %d negative, %d ties (%s)" % (npos, nneg, ties, a.tie))
    print("Fleiss' kappa over %d coders: %.3f" % (k, fleiss(votes, k)))
    print("pairwise agreement (coder A vs B):")
    for (ia, ca), (ib, cb) in itertools.combinations(list(enumerate(cols)), 2):
        agree = sum(1 for _, v in full if v[ia] == v[ib]) / max(1, len(full))
        flag = "   <-- CHECK: near-identical answers; are these really different models?" if agree >= a.identity_flag else ""
        print("  %s vs %s: %.1f%%%s" % (ca, cb, 100 * agree, flag))
    print("note: agreement on a binary label is high whenever one class is rare, so a flag is a prompt to compare")
    print("      the disagreements and the model identities, not proof. 100% between two models is the real alarm.")


if __name__ == "__main__":
    main()
