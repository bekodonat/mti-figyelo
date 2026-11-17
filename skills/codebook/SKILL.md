---
name: codebook
description: >-
  Format / write a DATA codebook — the documentation of a text-as-data dataset (corpus), following the
  ParlLawSpeech template. Gives the standard document structure (title page · introduction · coverage & data
  collection · data structure & variables · validation · data access · references · appendix) and the
  variable-documentation conventions: the core-vs-additional split (core = fields present in nearly every
  unit; additional = source-specific extras), per-dataset core-variable tables (two columns, monospace
  `variable` | plain Description, with a caption + a one-line "Data on …" header), a single unique cross-
  corpus linking identifier, format + encoding notes (e.g. .RDS/CSV, UTF-8), keeping the raw text beside the
  cleaned text for reproducibility/traceability, links back to the original source per record, and an explicit
  open licence (e.g. CC-BY 4.0). Invoke via /codebook or when the user says "write/format a codebook",
  "document the corpus/dataset", "data codebook", "variable codebook", "corpus documentation", "document the
  variables", "codebook structure", "describe the dataset's variables". This is the DATA-codebook (dataset
  documentation) sense — DISTINCT from a CODING codebook / classification scheme (CAP topics etc.). Worked
  example: the ParlLawSpeech codebook (Schwalbach, Hetzer, Proksch, Rauh & Sebők, v1.0, 2025;
  parllawspeech.org). Composes with /datavalidation (the validation half, its appendix) and /record-linkage
  (the linking identifier).
---

# /codebook — formatting a data codebook

A **data codebook** is a dataset's own documentation: what it covers, how it was
collected, and what every variable means. It is what lets a stranger — a reviewer, a
re-user, your later self — trust and navigate the data without reading the collection
code. (This is the *documentation* sense of "codebook", not a *coding* codebook /
classification scheme.)

Worked template throughout: the **ParlLawSpeech codebook** (Schwalbach, Hetzer, Proksch,
Rauh & Sebők 2025) — three linked corpora (speeches, bills, laws) for eight European
legislatures.

## Standard structure

1. **Title page** — corpus name · "Codebook" · authors · date · version (e.g. `VERSION: 1.0`) · project URL · funding/licence note.
2. **Introduction** — what the corpus is, why it matters, what is novel, and one sentence on what the codebook itself covers (coverage, collection, validation, variable definitions).
3. **Coverage & data collection** — a descriptive-statistics table (unit of analysis × count × #variables × time frame, by country/source), the case-selection rationale, and the collection method (e.g. per-archive scraping).
4. **Data structure & variables** — file format + encoding (e.g. `.RDS`, UTF-8); the **core/additional** rule; the unique linking identifier; then, per dataset, a **core-variable table** + an **additional-variables** prose paragraph.
5. **Validation** — a short prose summary of how the data was validated (the full workflow goes in an appendix → `/datavalidation`).
6. **Data access** — repository, licence (e.g. CC-BY 4.0), the canonical version.
7. **References · Acknowledgements**.
8. **Appendix — validation workflow** (`/datavalidation`).

## Variable-documentation conventions

- **Core vs additional.** Define **core** variables as those missing from at most a small,
  fixed number of units (PLS: "missing from at most two legislatures") — list them in a
  table that holds across the whole dataset. List **additional** (source-specific) variables
  in prose, noting which sources carry them. Listing the two separately is what makes a
  multi-source dataset navigable.
- **Core-variable table** — two columns: the **`variable`** name in monospace, and a plain
  one-line **Description**. Give it a caption ("Table N: Core variables of the X corpus")
  and a one-line header ("Data on …"). Keep descriptions terse and concrete (e.g.
  `procedure_ID` → "The unique identifier linking speeches, bills, and laws").
- **One linking identifier.** A single key that ties the dataset to its companions (PLS's
  `procedure_ID` links a speech → the bill it concerns → the law it became) turns separate
  tables into one navigable record. Name it, and document it first.
- **Format + encoding.** State the file format and that text is UTF-8 (flag exceptions).
- **Keep the raw text.** Ship `text_raw` beside the cleaned `text` so cleaning is reproducible
  and an error traces to the step that introduced it; include **links to the original** per
  record for traceability.
- **Dates** in a stated format (e.g. `YYYY-MM-DD`); **missing values** documented, not silently
  dropped.
- **Open licence** stated explicitly (PLS: CC-BY 4.0), with the repository as the canonical
  source.

## How the agent helps

Drafts the codebook from the data (profiling columns → candidate descriptions, detecting the
core/additional split, proposing the variable tables), and keeps it **in step as the dataset
changes** — a codebook that drifts from the data is worse than none. What it documents must
then survive `/datavalidation`: documentation is a claim about the data; validation makes the
claim true.
