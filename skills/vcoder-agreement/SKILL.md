---
name: vcoder-agreement
description: >-
  Check machine labels against your own hand coding before you count anything: match hand.csv to
  labels.csv by file, report exact agreement, Cohen's kappa, per-category precision and recall with the n
  and base rate of each category, the confusion matrix, and every mismatch, so you can read whether the
  codebook is unclear or the model is wrong; then decide what stays human. Ships agreement.py (standard
  library). Use when the user says "check the labels against me", "agreement", "kappa", "compare hand
  coding with the machine", or "/vcoder-agreement". Always trigger when the user runs /vcoder-agreement.
---

# vcoder-agreement — check before you count

Agreement tells you whether a second coder, working from the same codebook, lands on the same labels. It
does not tell you the labels are right; that is a question about the construct. But without it the counts
that follow are counts of nothing in particular. The order is fixed: agreement first, counts second.

## Workflow

1. **Hand-code a sample from the same codebook, blind.** Twenty to thirty files for a first check, a
   hundred or more for a paper. Code them yourself without looking at the machine's labels, into
   `hand.csv` with the same `file` and `code` columns as `labels.csv`.
2. **Align and compute.**
   ```bash
   python3 scripts/agreement.py hand.csv labels.csv --id file --code code
   ```
   It matches rows by file, reports how many matched, and prints: exact agreement; Cohen's kappa; per
   category the n in your hand coding, its base rate, the machine's precision and recall; the confusion
   matrix; and the list of mismatches.
3. **Read the kappa against the base rates.** Kappa corrects for agreement by chance. When one category
   dominates, exact agreement can be high while kappa sits near zero, which is the honest number. A
   category with fewer than ten hand-coded units gets no verdict yet; say so.
4. **Read every mismatch.** For each, one of three verdicts: the codebook is unclear (two readers could
   defensibly differ; fix the codebook, new version, re-run), the model is wrong (note the pattern: a
   near miss it keeps falling for, a length it truncates), or your hand code was wrong (correct `hand.csv`
   and record that you did).
5. **Fix, re-run, re-check on a fresh sample.** Never report agreement measured on the sample you tuned
   the codebook on. Draw new files for the check that counts.
6. **Decide what stays human.** Set a bar per category from its stakes in the argument, not one bar for
   all. A category below its bar is coded by people, or dropped, and the methods section says so.
7. **Report.** Exact agreement and kappa with n; the per-category table; the convention you read the
   numbers against (for kappa: above 0.8 strong, 0.6 to 0.8 moderate, below 0.6 weak, as a convention,
   not a law); the categories routed to people.

## Traps

- **A thin class.** 0.9 overall can hide 0.1 on the one category the argument rests on. Per category or
  nothing, with n beside every number.
- **Fluent and wrong.** A confident reason is not evidence. The sentence is; read it.
- **A leaked test.** If your hand-coded texts are public and old, the model may have seen them in training.
  Prefer a fresh or private sample for the check that counts.
- **Tuning on the test.** The sample you fixed the codebook on no longer tests anything.

## Output

The agreement report (numbers above, in one table per block) and `mismatches.csv` (file, hand code, machine
code, the sentence, your verdict). Read-only on both input files.

Companion skills: /vclassify (produces labels.csv), /vcodebook (the instrument you are testing),
/vmodel-bench (the same check across several candidate models), /vcalibrate (carry the measured error
into corrected rates and a regression).
