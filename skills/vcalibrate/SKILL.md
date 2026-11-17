---
name: vcalibrate
description: >-
  VCALIBRATE (vanilla calibrate-then-regress): the shareable, agent-neutral, lab-free recipe for measuring a
  concept in a large text corpus cheaply and correctly, then regressing on it. A cheap classifier scores every
  text, a score-stratified sample is coded blind by several large language models, their majority is the
  reference, the sample gives the classifier's sensitivity and specificity, each group's rate is corrected for
  classifier error (Rogan-Gladen, design-weighted, bootstrap intervals), and the corrected rates go into a
  group-year panel regression. Ships four standard-library scripts (sample.py, reference.py, correct.py,
  panel.py) and a self-test on synthetic data. Use ONLY when the user asks for vcalibrate or the
  vanilla/generic/shareable calibrate-then-regress workflow: "/vcalibrate", "vanilla calibrate", "correct a
  classifier's prevalence with an LLM-coded sample", "Rogan-Gladen with a stratified sample", "measure it cheaply
  and then regress". Always trigger when the user runs /vcalibrate.
---

# vcalibrate — measure it cheaply, correct it, then regress (vanilla)

The quantitative worked example behind "Agents decide, code does the work". The agent decides the design and
writes the instructions the coders follow; plain code does every count, draw, correction and regression; large
models read only a sample. Nothing here is specific to one field.

## The goal

You want the rate of some concept (a frame, a topic, a stance) per group and period across a corpus too big
for any large model to read, and then you want to ask whether that rate predicts something. A cheap classifier
can score every text but it makes errors, and its errors are not random: a classifier that over-flags makes
every group look more extreme and distorts comparisons. This workflow measures the classifier's error on a small
blind-coded sample and removes it from the group rates before any regression.

The worked example, described generically: a fine-tuned classifier scored 58,874 parliamentary speeches and
507,599 news sentences for a policy frame. For each legislature and topic, 300 items were drawn (stratified by
classifier score) and coded blind by three large language models; the majority was the reference. The sample gave
each classifier's sensitivity and specificity, each country's rate was corrected, and 80 country-years went into a
fixed-effects regression of the change in a democracy index 12 and 24 months later on the corrected prevalence.

## The pattern

```
cheap classifier scores EVERY text
   -> stratified sample (by score) drawn per group           sample.py
   -> blind coding by k large models, majority = reference   reference.py
   -> sensitivity / specificity from the sample (weighted)
   -> each group's rate corrected, bootstrap interval        correct.py
   -> group-year panel, lead changes, fixed effects          panel.py
   -> report RAW and CORRECTED, never raw alone
```

All scripts need only Python 3.9+ and read and write plain CSV. Run `python3 scripts/selftest.py` first: it
plants a known prevalence, classifier error and effect, and checks that the pipeline recovers them.

## Workflow

### Step 1: Define the construct and write the codebook

One concept, binary (present / absent). Write the codebook as the instructions the coders will receive:
a definition, two or three positive and negative examples, the edge cases that decide close calls, and the
answer format (a single 0 or 1). Pilot it by hand on 30 texts; fix the wording where you and the coders
disagree. A vague concept cannot be rescued by any correction.

### Step 2: Score every text with the cheap classifier

Produce `scored.csv` with one row per text: `id, group, score` (score between 0 and 1; add `year` or any other
column your cells need; a `text` column is allowed). The classifier reads everything; it is cheap. Keep the
score, not only the yes/no, because the sample is stratified on it and the threshold can be changed later.

### Step 3: Draw the stratified sample

```bash
python3 scripts/sample.py scored.csv --by group,year --n 300 --bins 5 --text-col text --coders 3 --seed 1
```

Within every cell (one value of the `--by` columns) the texts are cut into score bins and the 300 are shared
equally across bins, so the tails (the rare, informative cases) are not drowned by the bulk. Outputs:
`sample.csv` (with the stratum and a sampling weight = stratum size / items drawn) and `coding_sheet.csv` (ids and
text only, shuffled, no scores, blank coder columns). Give the coders only the sheet. A cell smaller than `--n` is
taken whole.

### Step 4: Blind coding by several large models

Send every item on the sheet to each of k coders (k odd, at least 3), each with the same codebook, and fill one
0/1 column per coder (`coder_1` ... `coder_k`). Example coder set, named generically: one frontier API model and
two open-weight models of different families. Notes:

- Use different model families so that errors are not shared; a majority of three copies is one opinion.
- Ask for a bare 0 or 1 (or a one-word answer you map to it). Put no tool-forcing or elaborate output schema on a
  one-token answer; it adds cost and failure modes.
- Set temperature to 0 where the model accepts it. Some current models refuse a temperature setting or think by
  default: switch thinking off for a labelling task unless you have shown it helps on your pilot, and record
  what each model actually ran with.
- Code in batches, with the codebook as a cached prefix (see Cost). Keep a log of model name, version string,
  date and settings per column.
- Humans can be one or more of the coders. A human-coded subsample is the best check on the whole design.

### Step 5: Build the reference label

```bash
python3 scripts/reference.py coded.csv
```

Majority vote per item. It reports pairwise agreement, Fleiss' kappa, ties (with an even number of coders a split
vote gets no reference and is dropped; do not break ties by coin) and incomplete rows. Read the agreement:

- Two coder columns that agree on more than about 90% of items are a flag. With a rare class, agreement is high
  anyway, so inspect the disagreements and confirm the columns really came from different models. If two
  "different" columns are near identical, suspect one server answering twice (a port or alias collision) and
  rerun before going on.
- Low kappa means the codebook is ambiguous, not that the models are bad: revise the codebook and recode.

### Step 6: Correct each group's rate

```bash
python3 scripts/correct.py --scored scored.csv --sample sample.csv --reference reference.csv \
    --threshold 0.5 --by group,year --error-by group --boot 500 --seed 1
```

For each cell the script reports the raw rate (share of the whole corpus at or above the threshold, a census
observed in full), the design-weighted sensitivity and specificity, the weighted sample prevalence, the
Rogan–Gladen corrected prevalence `(raw + specificity − 1) / (sensitivity + specificity − 1)` clipped to [0, 1],
and a bootstrap 95% interval that resamples inside strata, recomputes sensitivity and specificity, and redraws each cell's raw rate (binomial noise in how many of that cell's texts the classifier gets wrong). Without the redraw the interval runs too narrow (86% coverage in the self-test); with it, 97–98%. `--census-only` turns the redraw off.

- **Why weighted.** The sample is stratified on the score, so high-score items are over-represented among the
  positives. Unweighted sensitivity and specificity would be wrong in a known direction. Weights are the inverse
  inclusion probability per stratum.
- **`--error-by`.** Sensitivity and specificity can be pooled over a coarser unit than the cell (error rates per
  country, rates per country-year). Use it whenever 300 items per cell is too few to estimate errors cell by cell,
  and say so in the report. It assumes the classifier's error rates do not drift over the pooled periods; check
  this on a few high-count cells.
- **Weak classifiers.** The correction divides by `sensitivity + specificity − 1`. When that is small (the script
  warns below 0.3) the corrected rate is mostly noise: improve the classifier or the threshold rather than the
  statistics. If the sensitivity plus the specificity is at most one, no correction is possible.
- **Threshold.** Any threshold can be evaluated from the same sample, because the sample spans the whole score
  range. Pick it once, before looking at regression results.

### Step 7: Aggregate to a panel and regress

```bash
python3 scripts/panel.py --rates corrected.csv --outcome outcome.csv --x corrected --lags 1,2 --boot 999
python3 scripts/panel.py --rates corrected.csv --outcome outcome.csv --x raw_rate --lags 1,2   # for comparison
```

`outcome.csv` holds `group, year, value`. For every lag L the model is
`outcome[t+L] − outcome[t] = β · prevalence[t] + unit fixed effect + error`, estimated by OLS after subtracting
unit means. With annual data lag 1 is 12 months and lag 2 is 24. The script prints the coefficient, a
cluster-robust standard error (clusters are units) and a wild-cluster (Rademacher) bootstrap p-value with the null
imposed, which is the one to quote with few units. `--baseline` adds the outcome level at t as a control. The
script is a dependency-free reference. For real work you may prefer R (`fixest`, `fwildclusterboot`) or Python
`statsmodels`: feed them the same `corrected.csv`, and use the script to cross-check.

### Step 8: Report

Report raw and corrected side by side, with the intervals, the sample sizes, the sensitivity and specificity per
error unit, the agreement among coders, and the models, versions and settings used. Never raw alone. State the
design: stratified by score, N per cell, bins, threshold, seed. Say what the regression does not show: a lead
association in a small panel is not a causal estimate.

## Cost

The large models read only the sample, the classifier reads everything. In the worked example the sample is
300 items per cell over 100 cells, 30,000 items, about 5% of the 566,000 texts.

Anthropic first-party list prices per million tokens (input / output), as cached on 25 September 2026; check the
live pricing page before quoting: Haiku 4.5 $1 / $5, Sonnet 5.5 $2 / $10, Opus 5.5 $4 / $20. Two levers cut a
labelling bill further: **batch mode** (about half price, results within a day) and a **cached instruction
prefix** (the codebook is the same for every item; cached reads bill at a fraction of the normal input price).

Illustration, assuming 800 input tokens and 50 output tokens per item, batch prices, no caching:

| Model | 30,000-item sample | all 566,000 texts |
|---|---|---|
| Haiku 4.5 | about $16 | about $300 |
| Sonnet 5.5 | about $31 | about $600 |
| Opus 5.5 | about $62 | about $1,200 |

Three coders cost roughly three times the row you pick; mixing in open-weight models you run yourself lowers
that. The arithmetic: items × tokens ÷ 1,000,000 × price × 0.5 for batch. Recompute with your own token counts
(count a sample of real prompts) before budgeting.

## Pitfalls (each cost a real project time)

1. **Test-split contamination.** If the classifier's own test set shares texts with its training data, its
   reported accuracy is not evidence. This workflow does not use that test set at all: the sensitivity and
   specificity come from the fresh blind sample. Check that the sample ids are not in the training data.
2. **One model answering for another.** Two coder columns from "different" models that match almost item for
   item are usually one server behind two names (a shared port, a default alias). Run the identical-answer
   check in `reference.py` for every pair before trusting the majority.
3. **Seeded draws over unordered sets.** A random draw over a Python `set` or a dict built from a file in
   arbitrary order changes between runs even with a seed. The scripts sort cells, strata and ids before
   drawing; do the same in any code you add, and run every stochastic step twice to see that it reproduces.
4. **Rounding.** Keep full precision until the final table. Python's `round` and `"%.0f"` round half to even
   (2.5 prints 2); prose built from a table must quote the table's own printed precision.
5. **Coders see only text.** Never put the classifier score, the group or the year in the coder's prompt.
6. **Ties and dropped items change the weights.** The script recomputes weights over the items that kept a
   reference; report how many were dropped.
7. **Clipping hides trouble.** A corrected rate clipped at 0 or 1 usually means the raw rate sits outside what the
   estimated error rates allow. Look at the cell before reporting it.
8. **Correction assumes the error rates transfer.** The sample must cover the groups and periods being
   corrected, and the classifier's behaviour must not change across them (new outlets, a new vocabulary).
9. **Do not tune on the outcome.** Fix the construct, codebook, threshold and model list before the regression.

## What NOT to do

- Don't report the raw classifier rate as the finding.
- Don't give the coders the scores, or let any one coder be the classifier itself.
- Don't draw an unweighted random sample and then use unweighted error rates on a score-stratified one.
- Don't paper over a weak classifier with a bootstrap interval.
- Don't read causal meaning into a handful of country-years.

## Output format of the report

```
CALIBRATION REPORT — <concept> — <date>
Design: classifier <name/version>, threshold <t>; sample <N> per cell in <b> score bins (seed <s>);
        coders <k models, versions, settings>; reference = majority; ties dropped: <n>
Agreement: Fleiss kappa <x>; pairwise <min>–<max>%
Classifier error (per <unit>): sensitivity <a>–<b>, specificity <c>–<d>
Rates: raw <range> -> corrected <range>; cells flagged: <n>
Regression: lag 1 beta <b> (cluster SE <se>, wild-bootstrap p <p>, N <n>, units <g>); lag 2 ...
Raw-rate regression for comparison: ...
Limits: ...
```

## Gotchas

- Column names are conventions, not magic: `id`, `group`, `score`, and `year`/`value` in the panel step. Use
  `--by`, `--unit`, `--time`, `--x`, `--y` to rename.
- `--by` columns in `correct.py` must match those used in `sample.py`.
- A cell with no reference-positive (or no reference-negative) items in its error unit gets no estimate; widen
  `--error-by`.
- The wild bootstrap is seeded; vary `--seed` once to see that the p-value is stable at the precision you quote.
