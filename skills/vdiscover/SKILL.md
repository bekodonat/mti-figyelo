---
name: vdiscover
description: >-
  Explore a corpus before the codebook is fixed: cluster the documents into candidate themes (an embedding
  topic model such as BERTopic, or the bundled no-install TF-IDF script), choose the number of topics by a
  stated rule and report the neighbouring counts too, read the outlier bucket, name each theme from its
  representative documents, and hand the result to /vcodebook as candidate codes to be validated on
  documents the discovery never saw. Writes topics.csv, doc_topics.csv and a run log; changes no data.
  Use when the user says "what is in this corpus", "find the themes", "topic model", "cluster these texts",
  "I do not know my categories yet", "unsupervised", or "/vdiscover". Always trigger when the user runs
  /vdiscover.
---

# vdiscover — find the categories before you code them

Discovery is the work before measurement. A study that starts from a finished codebook has skipped the
hardest step, deciding what the categories are. This skill finds candidate categories in the corpus itself
and returns them as a draft, never as a finding (Grimmer, Roberts & Stewart 2022, Part III). It changes no
text. The three supervised moves (/vcodebook, /vclassify, /vcoder-agreement) come after it, on documents
the discovery never saw.

## When to use it, and when not

- Use it when there is no codebook yet, when a corpus is new to you, or when you suspect a fixed scheme
  misses a theme that is in the texts.
- Do not use it as a labeller. A topic is a cluster of documents that share vocabulary or meaning; a code
  is a decision rule a stranger can apply. When you already have a codebook, go to /vclassify.

## Workflow

1. **Fix the unit and clean the corpus.** One text file per unit (or a CSV with a text column), the same
   unit you would later code. Run /vdatavalidation first: duplicates become a topic of their own.
2. **Hold out before you look.** Split the corpus by a seeded shuffle: 70 percent for discovery, 30
   percent held out and never clustered (the script writes `holdout_ids.csv`). The held-out documents are
   where the scheme is later checked. A scheme tuned to a corpus will always seem to fit that corpus.
3. **Choose the representation.** Route A, an embedding topic model: a pinned open sentence-transformer
   turns each document into a vector that carries meaning, then BERTopic reduces, clusters and describes.
   Route B, the bundled script: TF-IDF vectors and spherical k-means, no packages, for a first look and for
   corpora of about 50 to 2,000 documents whose themes live in their shared vocabulary. Short texts and
   paraphrase need Route A.
4. **Pick the number of topics by a stated rule.** The script scans a range of k and picks the best
   silhouette (how much closer a document is to its own cluster than to the nearest other one); BERTopic
   grows clusters from `min_cluster_size`. Either way, report the chosen count and its neighbours
   (`k_scan.csv`). The count is a setting, not a discovery.
5. **Read before you name.** For each topic take the top terms and five representative documents. Name
   the topic from the documents, not from the term list. A model may propose names; you confirm them by
   reading. Keep the term list in the table so a reader can check the name.
6. **Read the outlier bucket.** Documents far from every centroid (the script's `outlier = 1`, BERTopic's
   topic `-1`) are evidence, not noise to hide: a missing theme, a corpus-boundary problem, or texts that
   are not what you thought you collected.
7. **Hunt the negative cases.** For each named theme, look for three documents assigned to it that do not
   fit the name. If they are easy to find, the theme is a mixture and the name is too broad.
8. **Write candidate codes, not findings.** Each surviving theme becomes a candidate code with a definition
   drawn from its representative documents. Run /vcodebook on them, /vclassify on the held-out 30 percent,
   and /vcoder-agreement against your own hand coding of those documents. A theme that does not survive
   this was a feature of the discovery sample.
9. **Log the run.** The model name and version (or the script), the seed, every parameter, N, the
   vocabulary size, the chosen k with its silhouette, the outlier share, the date. The script writes
   `run_log.txt`; copy the same facts into your project log for Route A.

## Route A: an embedding topic model

```bash
python3 -m venv .venv-topics && source .venv-topics/bin/activate
pip install bertopic sentence-transformers
```

```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer

docs = [...]                                    # the discovery split only, one string per unit
emb = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")   # a pinned open model; write its name and version in the log
vectors = emb.encode(docs, show_progress_bar=True)
model = BERTopic(
    embedding_model=emb,
    umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42),
    hdbscan_model=HDBSCAN(min_cluster_size=15, metric="euclidean", prediction_data=True),
    vectorizer_model=CountVectorizer(stop_words=my_stopwords, min_df=2),
    language="multilingual",                    # the default "english" strips every non-ASCII character before the term lists
    calculate_probabilities=False)
topics, _ = model.fit_transform(docs, vectors)
model.get_topic_info()                          # sizes and top terms; topic -1 is the outlier bucket
model.get_representative_docs(3)                # read these before naming topic 3
```

Set `min_cluster_size` low (10 to 20) for a corpus under a thousand documents and read the outlier share:
above a third means the clusters are too tight for the corpus. Fix `random_state` and run twice; the same
partition both times is the test that the run is reproducible.

## Route B: the bundled script, no packages

```bash
python3 scripts/discover_lite.py texts/ --kmin 3 --kmax 10 --holdout 0.3 --seed 1 --out discover_out
python3 scripts/discover_lite.py table.csv --text-col text --id-col id --k 6 --out discover_out
python3 scripts/discover_lite.py --selftest
```

TF-IDF weights over the words of the discovery split (minimum document frequency 2, words in more than
half the documents dropped, an optional stop-word file for the language), spherical k-means with several
restarts, k chosen by silhouette over the range, class-based TF-IDF top terms per topic, the five documents
nearest each centroid, and an outlier flag on the tenth of documents farthest from their own centroid.
Standard library only, Python 3.9 or newer; `--help` and `--selftest` answer.

## Outputs

| File | What it holds |
|---|---|
| `topics.csv` | topic, size, share, outliers, top terms, the representative documents' ids and first words |
| `doc_topics.csv` | one row per discovery document: id, topic, similarity to its centroid, outlier flag |
| `k_scan.csv` | every k tried with its silhouette; the chosen one marked |
| `outliers.csv` | the documents to read first |
| `holdout_ids.csv` | the documents the clustering never saw, for /vclassify and /vcoder-agreement |
| `run_log.txt` | parameters, seed, counts, the chosen k, the date |

## Traps

- Duplicates and near-duplicates form a topic of their own and inflate another's size: validate first.
- Titles alone are too short for stable topics; strip syndication tails (" | Site name") before anything.
- Default English settings on non-English text: stop words, accent stripping, English-only embeddings.
- A random seed left unset makes every run a different partition. Set it, run twice, compare.
- Topic names are bound to the corpus and period they came from. Reusing them on another period or source
  is a new measurement and needs its own check.
- Never validate the scheme on the documents that produced it. The hold-out is not optional.

## Composes with

/vdatavalidation before it. /vcodebook, /vclassify and /vcoder-agreement after it, on the held-out
documents. /vdescriptives for the prevalence table once the labels are checked.
