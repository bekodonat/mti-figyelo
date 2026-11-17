# vcalibrate — calibrate a classifier with a blind-coded sample, then regress (vanilla)

A skill for coding agents (the open SKILL.md format) for the quantitative case: measure a concept in a large
text corpus cheaply and correctly, then regress on it. A cheap classifier scores every text; a sample stratified
by classifier score is coded blind by several large language models; their majority is the reference; the sample
gives the classifier's sensitivity and specificity; each group's rate is corrected for classifier error and
carries a bootstrap interval; the corrected rates feed a panel regression.

## Install
1. Copy the `vcalibrate` folder into your agent's skills folder:
   - **Claude Code:** `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`), or a project's
     own `.claude/skills/`.
   - **Codex and other agents:** `~/.agents/skills/` (Windows: `%USERPROFILE%\.agents\skills\`).
2. Ask the agent for the skill by name (in Claude Code: `/vcalibrate`; in Codex: `$vcalibrate`), or run the
   scripts yourself, in this order (on Windows use `py` instead of `python3`):
   ```
   python3 scripts/selftest.py                 # proves the pipeline on synthetic data first
   python3 scripts/sample.py scored.csv --by group --n 300
   python3 scripts/reference.py coded.csv
   python3 scripts/correct.py --scored scored.csv --sample sample.csv --reference reference.csv
   python3 scripts/panel.py --rates corrected.csv --outcome outcome.csv
   ```

Needs only Python 3.9 or newer, and no packages. The regression script is a small, auditable reference; for
published work you can run the same `corrected.csv` through R or statsmodels.

## What it does
- **sample.py** draws N items per group, stratified by classifier score, with sampling weights, and writes a
  blind coding sheet that carries no scores.
- **reference.py** turns k coder columns into a majority label and reports pairwise agreement, Fleiss' kappa,
  ties, and a warning when two coders answer almost identically.
- **correct.py** gives each group's design-weighted sensitivity, specificity, raw rate, Rogan–Gladen corrected
  prevalence and a seeded bootstrap interval.
- **panel.py** builds lead changes of an outcome, fits unit fixed effects, and reports a cluster-robust SE and a
  wild-cluster bootstrap p-value.

## Tested
`scripts/selftest.py` plants 20 groups over 5 years (100 cells, 40,000 texts), a classifier with sensitivity and
specificity near 0.81, three simulated coders that are each 95% accurate, and an outcome driven by prevalence.
Result: the corrected rates' intervals cover the truth in 97–98% of cells across six synthetic runs (nominal 95%; was 86% before v2 added the raw-rate redraw) with a mean bias near +0.007 (the
raw rates are biased by about +0.11), runs repeat byte for byte, and the regression recovers the sign of the
planted coefficient.
