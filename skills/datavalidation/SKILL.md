---
name: datavalidation
description: >-
  Run a corpus DATA-VALIDATION workflow — the 5-step ParlLawSpeech procedure for validating a scraped /
  collected text dataset before it is analysed or released, run in the order the errors matter. (1) GENERAL
  COMPLETENESS & DUPLICATE CHECKS — uniqueness of IDs/text/links (context-aware: some duplicate texts are
  real, e.g. "Thank you."); completeness vs the original source AND an independent one, matched overall and by
  subgroup (speaker, committee, party, month, document type); every record has its text (no NA). (2) METADATA
  INSPECTION — standardise categorical fields to official forms (party names, roles); validate ID
  format/structure with regex; iterate. (3) CROSS-DATASET LINKING — full-join via shared IDs so counts
  reconcile; texts shouldn't overlap (except same-document cases → titles match); unnest comma-packed IDs
  wide→long + dedup; a count mismatch betrays a bad key. (4) TEXT CONTENT — iterate: sample (raw+clean, no
  repeats) → identify & correct errors (encoding/UTF-8, cleaning headers-footers, completeness, targeted-
  content e.g. two speeches in one, hyphenation) → save state & restart → test sentence tokenization vs a
  string count. (5) EXPLORATORY VALIDATION — descriptive scatterplots (length×punctuation, cleaned×raw length,
  length×#sentences, bill×law length) + automated methods (sentiment, Wordfish, unsupervised topic modeling,
  TF-IDF comparison) to surface anomalous rows. Invoke via /datavalidation or when the user says "validate the
  corpus/dataset", "data validation", "validation workflow", "completeness/duplicate checks", "validate
  scraped data", "anomaly/outlier detection in the corpus", "is the corpus clean / ready". Worked example: the
  ParlLawSpeech Data Validation Workflow (codebook appendix). Composes with /codebook (documents the validated
  result), /record-linkage (the join in step 3) and /data-provenance-checker (traces a derived table back to
  its raw source).
---

# /datavalidation — corpus data-validation workflow

Validate a collected/scraped text corpus **before** it is coded, analysed, or released.
Documentation (`/codebook`) is a *claim* about the data; this workflow is what makes the
claim true. Run the five steps roughly in the order the errors matter — cheap structural
checks first, expensive content checks last.

Worked template: the **ParlLawSpeech Data Validation Workflow** (appendix of the public ParlLawSpeech codebook, parllawspeech.org).

## 1 — General completeness & duplicate checks

- **Uniqueness.** Verify that columns which *should* be unique (IDs, text, links) contain no
  duplicates — but **context-aware**: some duplicate texts are genuine (short responses like
  "Thank you."), while duplicate long texts (e.g. bill bodies) need manual review.
- **Completeness of collection.** Confirm everything that should have been collected was.
  Validate against the **original source AND an independent one** (alternative websites, a
  media library, party sites, an official gazette) — errors in your scraper must not leak
  into your validation. Match the **number of observations overall and by subgroup**
  (speaker, committee, party, month, document type).
- **All texts present.** Confirm no record is missing its text (`!= NA`). This proves
  existence only — content quality is step 4.

## 2 — Metadata inspection

- **Standardise categorical fields.** Party names, speaker roles, etc. → their official
  forms, no spelling variants.
- **Validate IDs.** Check IDs follow the expected format/structure for the source; **regex**
  finds irregularities in structured fields efficiently. Apply fixes **iteratively**.

## 3 — Cross-dataset linking

- **Join on the shared key.** Full-join the linked datasets (e.g. bills↔laws,
  speeches↔bills); the joined count should reconcile with the totals. Texts should **not**
  overlap unless extracted from the same document (then titles should match).
- **Unnest multi-references.** When one record references many (a speech citing several bills
  as `19/50673/19, 19/4562/19`), **unnest wide→long** so each ID is its own row, then
  **dedup**. A joined count that exceeds the total betrays a key that matches nothing
  (investigate); legitimately unmatched items (a bill never debated) are expected and checked
  through their own link (bill → law).

## 4 — Text content (iterative)

Loop until a random sample (≥ ~10 texts) stops turning up new error patterns:

1. **Sample** — pull a random sample, save each row in **both raw and cleaned** forms; track
   picks so none repeats.
2. **Identify & correct** — compare cleaned ↔ raw ↔ original. Focus areas: **encoding**
   (UTF-8), **cleaning** (headers/footers/boilerplate removed — hard in some sources),
   **completeness** (start/end patterns), **targeted content** (only the intended text — catch
   "two speeches in one"), **hyphenation** (de-hyphenate split words). Fix the *preprocessing
   code*, not errors that live in the original document.
3. **Save & restart** — save state with row + iteration number, so progress is tracked and
   regressions are caught.
4. **Test tokenization** — count sentences in the cleaned text vs a string-count baseline;
   discrepancies flag lingering tokenization issues.

## 5 — Exploratory validation (anomaly detection)

- **Descriptive plots** — scatter **text length × punctuation count** (expect linear; outliers
  = mis-processed), **cleaned × raw length** (short cleaned = over-cleaning), **length ×
  #sentences** (tokenization accuracy), **bill length × law length** (mismatched/incomplete).
- **Automated text methods** on the aggregate — **sentiment** (unexpected → mislabel), **Wordfish**
  (odd textual patterns → processing errors), **unsupervised topic modeling** (irrelevant topics
  → contamination), **TF-IDF comparison** (unusually low-scoring tokens → missing/discrepant
  content).

## Stance

Each check is dull alone; together they separate a dataset that *looks* finished from one
that *is*. The agent runs the mechanical sweeps and surfaces the suspect rows; a human rules
on the context-dependent cases (is this duplicate real? is this anomaly an error or a finding?).
The validated result is then documented with `/codebook`.
