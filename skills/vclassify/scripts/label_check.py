#!/usr/bin/env python3
"""label_check.py — check a labels.csv produced by /vclassify against the folder of text files.

Usage:
  python3 label_check.py labels.csv --folder texts [--codes "A,B,C,NONE"] [--set-aside "NONE,UNREADABLE"]
                        [--file-col file] [--code-col code] [--sentence-col sentence] [--selftest]

Checks: every text file has exactly one row; every row names an existing file; every code is in the allowed
list (if given); every quoted sentence occurs verbatim in its file (whitespace and case normalised); and
the count closes: files in = rows coded + rows set aside. Exits 1 on any failure. Standard library only.
"""
import sys, os, csv, re, argparse, tempfile

def norm(s):
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("“", '"').replace("”", '"')).strip().lower()

def run(labels, folder, codes=None, set_aside=("NONE", "UNREADABLE"), file_col="file", code_col="code", sent_col="sentence"):
    fails = []
    files = sorted(f for f in os.listdir(folder) if not f.startswith(".") and not f.lower().endswith(".csv") and os.path.isfile(os.path.join(folder, f)))
    with open(labels, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for col in (file_col, code_col, sent_col):
        if rows and col not in rows[0]: fails.append(f"column missing: {col}"); return files, rows, fails, 0, 0
    seen = {}
    for i, r in enumerate(rows, 2):
        f = (r.get(file_col) or "").strip(); c = (r.get(code_col) or "").strip(); s = (r.get(sent_col) or "").strip()
        seen[f] = seen.get(f, 0) + 1
        if f not in files: fails.append(f"row {i}: file not in folder: {f}"); continue
        if codes and c not in codes: fails.append(f"row {i}: code not allowed: {c!r} ({f})")
        if not c: fails.append(f"row {i}: blank code ({f})")
        if c in set_aside: continue
        if not s: fails.append(f"row {i}: no sentence ({f})"); continue
        text = open(os.path.join(folder, f), encoding="utf-8", errors="replace").read()
        if norm(s) not in norm(text): fails.append(f"row {i}: sentence not found verbatim in {f}: {s[:60]!r}")
    for f in files:
        n = seen.get(f, 0)
        if n == 0: fails.append(f"no row for file: {f}")
        elif n > 1: fails.append(f"{n} rows for file: {f}")
    coded = sum(1 for r in rows if (r.get(code_col) or "").strip() not in set_aside and (r.get(code_col) or "").strip())
    aside = sum(1 for r in rows if (r.get(code_col) or "").strip() in set_aside)
    if coded + aside != len(files): fails.append(f"count does not close: files {len(files)} != coded {coded} + set aside {aside}")
    return files, rows, fails, coded, aside

def selftest():
    d0 = tempfile.mkdtemp(); d = os.path.join(d0, "texts"); os.makedirs(d)
    for name, txt in [("a.txt", "The council voted on housing.\nMembers argued for hours."), ("b.txt", "Nothing here is about policy."), ("c.txt", "A tax cut was proposed today.")]:
        open(os.path.join(d, name), "w").write(txt)
    lab = os.path.join(d0, "labels.csv")
    open(lab, "w").write('file,code,reason,sentence\na.txt,HOUSING,"about housing","The council voted on  housing."\nb.txt,NONE,"off topic",\nc.txt,TAX,"a tax cut","A tax cut was proposed today."\n')
    r = run(lab, d, codes=["HOUSING", "TAX", "NONE"]); assert r[2] == [], r[2]
    open(lab, "a").write('c.txt,TAX,"dup","A tax cut was proposed today."\n')
    r = run(lab, d, codes=["HOUSING", "TAX", "NONE"]); assert any("2 rows" in x for x in r[2]) and any("count" in x for x in r[2]), r[2]
    open(lab, "w").write('file,code,reason,sentence\na.txt,HOUSING,"x","Members voted on housing."\nb.txt,NONE,"",\nc.txt,SPORT,"x","A tax cut was proposed today."\n')
    r = run(lab, d, codes=["HOUSING", "TAX", "NONE"]); assert any("not found verbatim" in x for x in r[2]) and any("not allowed" in x for x in r[2]), r[2]
    print("selftest ok")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("labels", nargs="?"); ap.add_argument("--folder"); ap.add_argument("--codes", default="")
    ap.add_argument("--set-aside", default="NONE,UNREADABLE"); ap.add_argument("--file-col", default="file")
    ap.add_argument("--code-col", default="code"); ap.add_argument("--sentence-col", default="sentence"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); return
    if not a.labels or not a.folder: ap.error("labels.csv and --folder are required")
    codes = [c.strip() for c in a.codes.split(",") if c.strip()] or None
    aside = tuple(c.strip() for c in a.set_aside.split(",") if c.strip())
    files, rows, fails, coded, aside_n = run(a.labels, a.folder, codes, aside, a.file_col, a.code_col, a.sentence_col)
    print(f"files in folder: {len(files)} · rows: {len(rows)} · coded: {coded} · set aside: {aside_n}")
    for f in fails: print("FAIL", f)
    print("failures:", len(fails)); sys.exit(1 if fails else 0)

if __name__ == "__main__": main()
