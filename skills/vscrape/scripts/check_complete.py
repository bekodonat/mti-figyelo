#!/usr/bin/env python3
"""check_complete.py - does the extracted table reconcile with the official counts? (Python 3.9+, stdlib only)

  python3 check_complete.py rows.csv expected.csv
  python3 check_complete.py rows.csv expected.csv --group-col jurisdiction --id-col amendment_id

rows.csv      one row per item, with a group column (default 'group'), e.g. the jurisdiction.
expected.csv  columns: group, official_count, optional explained_count (items you know exist but could
              not extract, each with a written reason: repealed, never published, scan unreadable ...).

For every group it prints  captured + explained = total  against the official count, and exits with
status 1 if ANY group does not reconcile, or if rows carry a group the expected file does not list.
With --id-col, duplicate ids inside a group are reported and counted once.
"""
import argparse, csv, sys
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rows")
    ap.add_argument("expected")
    ap.add_argument("--group-col", default="group")
    ap.add_argument("--id-col", default=None, help="column that identifies an item; duplicates counted once")
    ap.add_argument("--official-col", default="official_count")
    ap.add_argument("--explained-col", default="explained_count")
    a = ap.parse_args()

    ids, plain, dups = defaultdict(set), Counter(), Counter()
    with open(a.rows, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        if a.group_col not in (rd.fieldnames or []):
            sys.exit(f"rows file has no column '{a.group_col}' (has: {rd.fieldnames})")
        if a.id_col and a.id_col not in rd.fieldnames:
            sys.exit(f"rows file has no column '{a.id_col}'")
        for r in rd:
            g = (r[a.group_col] or "").strip()
            if a.id_col:
                k = (r[a.id_col] or "").strip()
                if k in ids[g]:
                    dups[g] += 1
                ids[g].add(k)
            plain[g] += 1
    captured = {g: len(s) for g, s in ids.items()} if a.id_col else dict(plain)

    exp = {}
    with open(a.expected, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        for r in rd:
            g = (r["group"] if "group" in r else r[a.group_col]).strip()
            exp[g] = (int(r[a.official_col]), int((r.get(a.explained_col) or "0").strip() or 0))

    bad = 0
    print(f"{'group':<24}{'captured':>9}{'explained':>10}{'total':>7}{'official':>9}{'gap':>6}  status")
    for g in sorted(set(exp) | set(captured)):
        c = captured.get(g, 0)
        if g not in exp:
            print(f"{g:<24}{c:>9}{'-':>10}{'-':>7}{'?':>9}{'-':>6}  NOT IN EXPECTED FILE")
            bad += 1
            continue
        off, ex = exp[g]
        gap = off - (c + ex)
        status = "ok" if gap == 0 else ("SHORT by %d" % gap if gap > 0 else "OVER by %d" % -gap)
        if dups.get(g):
            status += f" ({dups[g]} duplicate ids)"
        bad += gap != 0
        print(f"{g:<24}{c:>9}{ex:>10}{c + ex:>7}{off:>9}{gap:>6}  {status}")
    print(f"\n{'ALL GROUPS RECONCILE' if not bad else str(bad) + ' group(s) do NOT reconcile'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
