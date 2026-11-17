#!/usr/bin/env python3
"""discover_lite.py — candidate themes from a folder of texts, with no packages: TF-IDF vectors, spherical
k-means with restarts, k chosen by silhouette over a range, class-based TF-IDF top terms, representative
documents, an outlier bucket to read, and a hold-out split the clustering never sees.

Usage:
  python3 discover_lite.py FOLDER_OR_CSV [--text-col TEXT] [--id-col ID] [--k K | --kmin 3 --kmax 10]
                           [--holdout 0.3] [--seed 1] [--min-df 2] [--max-df 0.5] [--stopwords FILE]
                           [--top-terms 10] [--reps 5] [--out discover_out]
  python3 discover_lite.py --selftest

FOLDER holds one text file per document (.txt or .md; dot files and .csv are skipped); a .csv path needs
--text-col and takes --id-col (else the row number). Writes topics.csv, doc_topics.csv, k_scan.csv,
outliers.csv, holdout_ids.csv and run_log.txt into --out. Exit 2 when fewer than 12 documents remain for
discovery. Standard library only, Python 3.9+.
"""
import sys, os, re, csv, math, random, argparse, tempfile, datetime
from collections import Counter, defaultdict

TOKEN = re.compile(r"[^\W\d_]{2,}")
STOP = set("""a an the and or but if of to in on at by for with from as is are was were be been being am do does did
this that these those it its he she they them his her their we you your our i me my not no nor so than then there
here when where which who whom what why how all any both each few more most other some such only own same too very
can will just also into over under about after before again further once out up down off while because until
has have had having s t can't don't""".split())

def tokenize(text, stop):
    return [t for t in (m.group(0).lower() for m in TOKEN.finditer(text)) if t not in stop]

def load(path, text_col=None, id_col=None):
    docs = []
    if os.path.isdir(path):
        for f in sorted(os.listdir(path)):
            p = os.path.join(path, f)
            if f.startswith(".") or f.lower().endswith(".csv") or not os.path.isfile(p): continue
            try: t = open(p, encoding="utf-8").read()
            except UnicodeDecodeError: continue
            if t.strip(): docs.append((f, t))
    else:
        if not text_col: sys.exit("a CSV needs --text-col")
        with open(path, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.DictReader(fh), 1):
                t = (row.get(text_col) or "").strip()
                if t: docs.append((str(row.get(id_col) or i) if id_col else str(i), t))
    return docs

def vectors_for(tokens_by_doc, min_df, max_df):
    n = len(tokens_by_doc); df = Counter()
    for toks in tokens_by_doc: df.update(set(toks))
    vocab = {t for t, d in df.items() if d >= min_df and d <= max_df * n}
    idf = {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in vocab}
    vecs = []
    for toks in tokens_by_doc:
        c = Counter(t for t in toks if t in vocab); v = {t: (1 + math.log(k)) * idf[t] for t, k in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / norm for t, x in v.items()})
    return vecs, vocab

def dot(a, b):
    if len(a) > len(b): a, b = b, a
    return sum(x * b.get(t, 0.0) for t, x in a.items())

def normalize(v):
    norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {t: x / norm for t, x in v.items()}

def kmeans(vecs, k, rng, iters=50):
    n = len(vecs); first = rng.randrange(n); centers = [dict(vecs[first])]
    best_sim = [dot(v, centers[0]) for v in vecs]
    while len(centers) < k:                                    # k-means++ seeding on cosine distance
        w = [(1 - s) ** 2 for s in best_sim]; tot = sum(w)
        if tot <= 0: idx = rng.randrange(n)
        else:
            r = rng.random() * tot; acc = 0.0; idx = n - 1
            for i, x in enumerate(w):
                acc += x
                if acc >= r: idx = i; break
        centers.append(dict(vecs[idx])); best_sim = [max(s, dot(vecs[i], centers[-1])) for i, s in enumerate(best_sim)]
    labels = [-1] * n
    for _ in range(iters):
        new = []
        for v in vecs:
            sims = [dot(v, c) for c in centers]; new.append(max(range(k), key=lambda j: sims[j]))
        if new == labels: break
        labels = new
        for j in range(k):
            members = [vecs[i] for i in range(n) if labels[i] == j]
            if not members:                                      # empty cluster: reseed with the worst-fitting document
                far = min(range(n), key=lambda i: dot(vecs[i], centers[labels[i]])); members = [vecs[far]]; labels[far] = j
            acc = defaultdict(float)
            for m in members:
                for t, x in m.items(): acc[t] += x
            centers[j] = normalize(acc)
    sims = [dot(vecs[i], centers[labels[i]]) for i in range(n)]
    return labels, centers, sims

def silhouette(vecs, labels, rng, sample=400):
    idx = list(range(len(vecs)))
    if len(idx) > sample: idx = sorted(rng.sample(idx, sample))
    S = {}
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            d = 1 - dot(vecs[idx[a]], vecs[idx[b]]); S[(idx[a], idx[b])] = d; S[(idx[b], idx[a])] = d
    by = defaultdict(list)
    for i in idx: by[labels[i]].append(i)
    vals = []
    for i in idx:
        own = [j for j in by[labels[i]] if j != i]
        if not own: vals.append(0.0); continue
        a = sum(S[(i, j)] for j in own) / len(own)
        b = min(sum(S[(i, j)] for j in others) / len(others) for lab, others in by.items() if lab != labels[i])
        vals.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return sum(vals) / len(vals)

def ctfidf(tokens_by_doc, labels, k, top):
    per = [Counter() for _ in range(k)]; total = Counter()
    for toks, lab in zip(tokens_by_doc, labels): per[lab].update(toks); total.update(toks)
    avg = sum(sum(c.values()) for c in per) / k
    out = []
    for c in per:
        size = sum(c.values()) or 1
        scores = {t: (n / size) * math.log(1 + avg / total[t]) for t, n in c.items()}
        out.append([t for t, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:top]])
    return out

def run(docs, k=None, kmin=3, kmax=10, holdout=0.3, seed=1, min_df=2, max_df=0.5, stop_extra=(), top=10, reps=5, out="discover_out", argv=""):
    rng = random.Random(seed); order = list(range(len(docs))); rng.shuffle(order)
    n_hold = int(round(holdout * len(docs))); hold = sorted(order[:n_hold]); disc = sorted(order[n_hold:])
    if len(disc) < 12: sys.exit(f"too few documents for discovery: {len(disc)} (need 12); lower --holdout or add texts")
    stop = STOP | set(stop_extra)
    ids = [docs[i][0] for i in disc]; texts = [docs[i][1] for i in disc]
    toks = [tokenize(t, stop) for t in texts]
    vecs, vocab = vectors_for(toks, min_df, max_df)
    if len(vocab) < 20: sys.exit(f"vocabulary too small after pruning: {len(vocab)} terms; lower --min-df or check the texts")
    n = len(vecs); scan = []
    ks = [k] if k else [x for x in range(kmin, kmax + 1) if x >= 2 and x <= max(2, n // 4)]
    if not ks: ks = [2]
    best = None
    for kk in ks:
        cand = None
        for restart in range(3):
            labels, centers, sims = kmeans(vecs, kk, random.Random(seed * 1000 + kk * 10 + restart))
            fit = sum(sims)
            if cand is None or fit > cand[0]: cand = (fit, labels, centers, sims)
        sil = silhouette(vecs, cand[1], random.Random(seed)) if kk > 1 else 0.0
        scan.append((kk, sil))
        if best is None or sil > best[0] + 1e-12: best = (sil, kk, cand[1], cand[2], cand[3])
    sil, kbest, labels, centers, sims = best
    thresh = sorted(sims)[max(0, int(0.1 * n) - 1)]
    outlier = [1 if (s <= thresh or s < 0.05) else 0 for s in sims]
    terms = ctfidf(toks, labels, kbest, top)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "doc_topics.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["id", "topic", "similarity", "outlier", "n_tokens"])
        for i in range(n): w.writerow([ids[i], labels[i], f"{sims[i]:.4f}", outlier[i], len(toks[i])])
    rows = []
    for j in range(kbest):
        members = [i for i in range(n) if labels[i] == j]
        top_docs = sorted(members, key=lambda i: -sims[i])[:reps]
        rows.append([j, len(members), f"{len(members) / n:.3f}", sum(outlier[i] for i in members), " ".join(terms[j]),
                     "|".join(ids[i] for i in top_docs), " || ".join(re.sub(r"\s+", " ", texts[i])[:80] for i in top_docs)])
    with open(os.path.join(out, "topics.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["topic", "size", "share", "outliers", "top_terms", "representative_ids", "representative_first_words"]); w.writerows(rows)
    with open(os.path.join(out, "k_scan.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["k", "silhouette", "chosen"]); [w.writerow([kk, f"{s:.4f}", 1 if kk == kbest else 0]) for kk, s in scan]
    with open(os.path.join(out, "outliers.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["id", "topic", "similarity", "first_words"])
        for i in sorted((i for i in range(n) if outlier[i]), key=lambda i: sims[i]): w.writerow([ids[i], labels[i], f"{sims[i]:.4f}", re.sub(r"\s+", " ", texts[i])[:100]])
    with open(os.path.join(out, "holdout_ids.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["id"]); [w.writerow([docs[i][0]]) for i in hold]
    log = (f"discover_lite run {datetime.datetime.now():%Y-%m-%d %H:%M}\ncommand: {argv}\ndocuments: {len(docs)} total, {n} discovery, {len(hold)} held out "
           f"(holdout {holdout}, seed {seed})\nvocabulary: {len(vocab)} terms (min_df {min_df}, max_df {max_df}, {len(stop_extra)} extra stop words)\n"
           f"k rule: {'fixed k' if k else f'best silhouette over {ks[0]}..{ks[-1]}'}; chosen k = {kbest}, silhouette {sil:.4f}\n"
           f"outliers: {sum(outlier)} of {n} ({sum(outlier) / n:.1%}); the count is a setting, not a discovery: read k_scan.csv\n")
    open(os.path.join(out, "run_log.txt"), "w", encoding="utf-8").write(log)
    return {"k": kbest, "silhouette": sil, "labels": labels, "ids": ids, "scan": scan, "n": n, "hold": len(hold), "outliers": sum(outlier), "terms": terms, "log": log}

def selftest():
    themes = [("farm", "harvest tractor wheat barley soil rain seed cattle barn pasture fence plough orchard dairy grain silo acre crop fertiliser meadow".split()),
              ("bank", "interest mortgage deposit loan credit bond equity dividend ledger broker portfolio inflation yield currency audit treasury invoice capital margin asset".split()),
              ("band", "guitar drummer chorus melody concert album rhythm vocal bass studio lyric encore tempo harmony stage tour riff ballad orchestra violin".split())]
    filler = "the of and to in a is for with on".split()
    rng = random.Random(7); docs = []
    for name, vocab in themes:
        for i in range(20):
            words = [rng.choice(vocab) for _ in range(rng.randint(14, 22))] + [rng.choice(filler) for _ in range(6)]; rng.shuffle(words)
            docs.append((f"{name}_{i:02d}.txt", " ".join(words) + "."))
    with tempfile.TemporaryDirectory() as td:
        folder = os.path.join(td, "texts"); os.makedirs(folder)
        for f, t in docs: open(os.path.join(folder, f), "w", encoding="utf-8").write(t)
        loaded = load(folder); assert len(loaded) == 60, len(loaded)
        r1 = run(loaded, kmin=2, kmax=6, holdout=0.3, seed=1, out=os.path.join(td, "o1"), argv="selftest")
        r2 = run(loaded, kmin=2, kmax=6, holdout=0.3, seed=1, out=os.path.join(td, "o2"), argv="selftest")
        assert r1["k"] == 3, ("k", r1["k"], r1["scan"])
        assert r1["labels"] == r2["labels"] and r1["ids"] == r2["ids"], "not deterministic for one seed"
        by = defaultdict(Counter)
        for id_, lab in zip(r1["ids"], r1["labels"]): by[lab][id_.split("_")[0]] += 1
        purity = sum(c.most_common(1)[0][1] for c in by.values()) / r1["n"]; assert purity >= 0.95, purity
        for f in ("topics.csv", "doc_topics.csv", "k_scan.csv", "outliers.csv", "holdout_ids.csv", "run_log.txt"): assert os.path.exists(os.path.join(td, "o1", f)), f
        assert r1["hold"] == 18 and r1["n"] == 42, (r1["hold"], r1["n"])
        assert all(any(t in vocab for t in terms) for terms in r1["terms"] for _, vocab in [max(themes, key=lambda th: sum(x in th[1] for x in terms))]), r1["terms"]
    print(f"selftest ok: k=3 chosen over 2..6, purity {purity:.2f}, 42 discovery + 18 held out, deterministic for one seed")

def main():
    ap = argparse.ArgumentParser(description="candidate themes from a corpus: TF-IDF + spherical k-means, silhouette-chosen k, outliers, hold-out")
    ap.add_argument("path", nargs="?", help="folder of text files, or a CSV")
    ap.add_argument("--text-col"); ap.add_argument("--id-col")
    ap.add_argument("--k", type=int); ap.add_argument("--kmin", type=int, default=3); ap.add_argument("--kmax", type=int, default=10)
    ap.add_argument("--holdout", type=float, default=0.3); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--min-df", type=int, default=2); ap.add_argument("--max-df", type=float, default=0.5)
    ap.add_argument("--stopwords", help="file with one stop word per line (add the function words of your language)")
    ap.add_argument("--top-terms", type=int, default=10); ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--out", default="discover_out"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); return
    if not a.path: ap.print_help(); sys.exit(2)
    extra = [l.strip().lower() for l in open(a.stopwords, encoding="utf-8")] if a.stopwords else []
    docs = load(a.path, a.text_col, a.id_col)
    r = run(docs, k=a.k, kmin=a.kmin, kmax=a.kmax, holdout=a.holdout, seed=a.seed, min_df=a.min_df, max_df=a.max_df,
            stop_extra=[x for x in extra if x], top=a.top_terms, reps=a.reps, out=a.out, argv=" ".join(sys.argv))
    print(r["log"]); print("k_scan:", ", ".join(f"k={kk}: {s:.3f}" for kk, s in r["scan"]))
    for j, terms in enumerate(r["terms"]): print(f"topic {j}: {sum(1 for l in r['labels'] if l == j)} docs · {' '.join(terms[:8])}")
    print(f"written to {a.out}/: topics.csv doc_topics.csv k_scan.csv outliers.csv holdout_ids.csv run_log.txt")

if __name__ == "__main__": main()
