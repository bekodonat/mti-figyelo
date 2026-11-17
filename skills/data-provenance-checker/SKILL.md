---
name: data-provenance-checker
description: >-
  Audit whether a DERIVED analysis dataset (the built, deduplicated, coded table that your numbers come
  from) can be faithfully rebuilt from its raw source(s). Catches the four silent killers of a derived
  corpus: schema MISALIGNMENT (a load bug shifts columns), DOUBLE-COUNTS (the same record captured by two
  scrapes survives deduplication twice), CODING DRIFT (a mangled row gets mis-classified) and silent ROW
  LOSS (a deduplication merges genuinely distinct records). Traces every derived row back to a raw record,
  proves any defect before acting, then rebuilds the table from source into a NEW versioned file with
  provenance columns. Invoke via /data-provenance-checker or when the user says "data provenance", "verify
  the master table from the raw data", "is this dataset reconstructable from the raw export", "check for
  double-counts", "did we lose rows", "rebuild the table verifiably". Real data only; never invent a count.
---

# /data-provenance-checker — is the built table faithful to, and rebuildable from, its raw source?

A **derived table** (deduplicated, coded, filtered to a time window, assembled from one or more raw
scrapes or exports) is what your tables and figures actually count. Between the raw source and that
table sit load bugs, schema drift, deduplication and coding: each a place where it silently drifts from
the truth. This skill audits that lineage, proves any defect, and rebuilds the table from source.

**The question, answered with evidence:** can I reconstruct this table from the raw source, and does every
row trace back to a real source record? Every count is read from the data as it is now, never from notes.

## Workflow

1. **Pin the derived table and read it live.** Shape (rows × columns), header, coded count, counts per
   group. Notes about the table are pointers, not truth: re-read the data.
2. **Find the ground-truth source(s).** Prefer the raw export in its own native layout over any
   consolidated or transformed copy; bugs live in the transform. If the raw file is unreachable, say so and
   use the closest faithful copy.
3. **Check schema alignment per source.** Read each source raw, without padding empty cells. Make a
   histogram of row lengths (several lengths ⇒ mixed rows ⇒ a shift is likely). Compare headers across
   sources: a column added in one copy is where rows loaded from another copy get shifted. Look for the
   shift signature: a numeric column holding text, a text column holding a number. Anchor on a field you
   can recognise (a URL, an ISO date, an id) and write a deterministic rule for "this row is shifted".
4. **Establish ground truth for the suspect rows.** Join them to an independent clean copy on the natural
   key (canonical URL, id or content hash: strip query strings and trailing slashes, lowercase). Classify
   each: (a) recoverable in place (just offset); (b) duplicate of a clean row (same key + same timestamp +
   same content ⇒ the table counts it twice); (c) genuinely distinct (keep it, un-shifted). Prove each class
   with field-by-field checks, not with totals.
5. **Try to refute your own finding before acting** when it changes a headline number or overturns an
   earlier note: re-derive it from the source a second way (or have a second agent do it blind), look for a
   suspect row that is really distinct, and look for any distinct record the rebuild would lose. Any
   disagreement ⇒ stop and re-diagnose.
6. **Rebuild from source.** Read each source in its own layout (detect columns by header, not position);
   un-shift offset rows; fix encoding damage (mojibake) before keying; deduplicate on the natural key and
   never merge two distinct keys; carry coding from the clean, already-coded rows rather than re-coding a
   mangled row; add provenance columns (`source_files`, `n_captures`); apply the scope/window filter last.
7. **Write non-destructively.** Save the corrected table as a NEW file or tab (`<name>_v2`), keep the
   original, keep the rebuild script: the script is the proof that the table is rebuildable from source.
   Recount and assert: 0 misaligned rows, keys unique, 100% of rows linked to a source, and a diff against
   the old table (rows added, removed, re-coded).
8. **Report the change and hold the knock-on edits.** If the number of observations changes, say so plainly
   and update the paper's tables, figures and text only after the researcher agrees.

## Output format

```
## Provenance audit — <table name>
Verdict: FAITHFUL ✅ | DEFECT FOUND 🔴 — <one line>
Sources: <raw A (native)> · <raw B (native)> · <copy C (consolidated — defect here)>
Defect: <schema shift | double-count | coding drift | row loss> — <mechanism, one sentence>
Evidence: <the identity check that proves it>

| metric          | current table | rebuilt from source | Δ |
|-----------------|--------------:|--------------------:|--:|
| rows            |               |                     |   |
| coded           |               |                     |   |
| misaligned rows |               | 0                   |   |

Written: <new file> (original kept) · rebuild script <path>
Held for sign-off: <which numbers in the paper change>
```

## What NOT to do
- Never deduplicate on a key that merges genuinely distinct records; prove the key is unique per record first.
- Never overwrite the original table; write a new version and keep the old one.
- Never trust a documented count or an earlier "don't touch this" note without re-reading the data.
- Never re-code a misaligned or garbled row; take the code from its clean twin.
- Never invent a count to make totals agree.

## A typical case (anonymised)
A social-media table was flagged "a few thousand rows misaligned, but they are distinct posts, do not
rebuild". The audit found that one source had been loaded into a wider layout without the extra column, so
every field sat one cell to the left and the URL fell into the text column. Every shifted URL existed,
correctly aligned, in another raw export, with the same timestamp and the same engagement figures: they were
duplicates, not distinct posts, and deduplication had missed them only because the URL was in the wrong
column. The duplicate copies were also the worse ones (garbled text, coded as "no content"). The rebuilt
table was about 10% smaller, had 0 misaligned rows, and every row was traced to a raw record; the earlier
"distinct posts" note had been a misdiagnosis.
