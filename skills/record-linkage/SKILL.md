---
name: record-linkage
description: >-
  Link structured datasets on a shared key — the join where structured data earns its power and most easily
  goes wrong. Declares the EXPECTED CARDINALITY of the join (1:1, many:1, 1:many), checks the MATCH RATE, and
  surfaces the two failure modes before they corrupt the n: spurious matches (two distinct units merged
  because they share a key value) and missed matches (the same unit recorded differently in each source and
  silently dropped). Handles both the easy case — an exact join on a clean key — and the hard one — fuzzy /
  probabilistic matching on names, dates, or near-duplicate identifiers, which is a small research project
  with its own error rates. Reports how many rows survived the join, how many duplicated, and how many failed
  to match, so the join's effect on the dataset is visible rather than assumed. Invoke via /record-linkage or
  when the user says "link / merge datasets", "join on a key", "record linkage", "entity resolution", "fuzzy /
  probabilistic match", "deduplicate records", "match people across registers", "the join changed my n", or
  "how many rows matched". The agent proposes the match and reports the cardinality, match rate, unmatched,
  and duplicates; whether the surviving pairs are the RIGHT ones is the researcher's judgment to make and
  document. Grounding: Christen (2012); Fellegi & Sunter (1969). Composes with /datavalidation (step 3, cross-
  dataset linking) and /codebook (records the linking key).
---

# /record-linkage — join datasets without corrupting the n

A join silently changes the dataset. This skill makes that change visible.

## Steps

1. **Declare the cardinality** you expect — **1:1**, **many:1**, or **1:many** — *before*
   joining. A join that returns a different cardinality than expected is a bug, not a result.
2. **Exact vs fuzzy.** If the key is clean and shared, do the exact join. If it isn't —
   names, dates, near-duplicate IDs — treat **fuzzy / probabilistic** matching as its own
   task with its own error rates (false matches vs missed matches), and tune the threshold
   deliberately.
3. **Report the join's effect:** rows in each source, rows matched, **match rate**, rows that
   **duplicated** (one-to-many blow-up), and rows that **failed to match** and would be
   dropped. A bad join inflates with spurious pairs or loses rows that should have matched —
   both invisible unless counted.
4. **Inspect the failures.** Sample the unmatched and the duplicated rows; many "non-matches"
   are the same unit written two ways ("J. Novák" / "János Novak").
5. **Verdict.** Whether the surviving pairs are the right ones — not merely how many survived
   — is the researcher's judgment, and is documented alongside the dataset.
