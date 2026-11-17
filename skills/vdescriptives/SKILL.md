---
name: vdescriptives
description: >-
  Descriptive statistics for an empirical paper (vanilla): how to describe the data and show a few tables
  and figures relating the explanatory variable to the outcome BEFORE the model. Builds the presentation
  from the data or audits an existing one: the sample funnel, the outcome's distribution, its categories,
  the explanatory variable and the variation that identifies its effect, a bivariate preview, the summary
  statistics table, at most two figures, and an explicitly descriptive framing. Use when the user says
  "descriptive statistics", "describe the data", "Table 1", "summary statistics", "a few IV–DV tables", or
  "vdescriptives". Always trigger when the user runs /vdescriptives.
---

# vdescriptives — describe the data before the model

The layer between Data & Methods and Results: the reader sees what was analysed and the raw pattern
before any regression. Build it from the data, or audit an existing one. Read-only audit by default.

## Eight components

| # | Component | What it establishes | Form |
|---|---|---|---|
| 1 | Sample funnel | Raw units → after filtering → analysed N, at each level (e.g. documents → sentences → units × periods). | prose, optional table |
| 2 | Outcome | Its overall level and its split by the main grouping (domain, country), and how the measure is built (binary, count, share). | table + prose |
| 3 | Categories | If the outcome has categories, how cases spread across them. | table |
| 4 | Explanatory variable | Its distribution, and the variation that identifies its effect (e.g. units observed under both conditions). | table |
| 5 | Bivariate preview | The outcome by level of the explanatory variable or group: the headline pattern, without the model. | table or figure |
| 6 | Summary statistics | Every model variable with N, mean, SD, min, max. | Table 1 |
| 7 | Figures | At most two: the outcome over time by group, and by the explanatory variable. | figures |
| 8 | Framing | Stated as description, not as the causal estimate; sample and coverage caveats. | prose |

The minimum: the outcome table (2), the explanatory-variable table (4), the bivariate preview (5) and
the summary statistics (6).

## Placement and length
A short description of the data can close the methods section; the tables, the bivariate preview and the
figures open Results, before the regression tables. Follow the target journal. Prose stays short (about
150–400 words): state the headline and point to the table; never walk through a table cell by cell.
Captions short; a note under each table gives the source and the base.

## Build
1. Pin the outcome, explanatory variable, controls, unit and analysed sample from the methods section.
2. Compute every number from the analysed data with a script, and keep the script with the project. Ask
   for the script that draws each table and figure, never for the figure itself; run it twice and keep it
   beside the data. The same figure both times is the test that it is reproducible.
3. Draft the prose, the tables and up to two figure specifications.
4. Insert into the manuscript only when asked, as real tables, marked for review.

## Audit
Map each paragraph and table to the eight components and score them ✅ · 🟡 · 🔴 · n/a. Flag a regression
presented as "descriptives", a missing Table 1, an outcome level with no breakdown, the identifying
variation not shown, numbers that do not match the data or the regression tables, a table narrated cell by
cell.

## What not to do
Don't run or report the regression here. Don't type numbers by hand; compute them. Don't fill a cell you
have not computed: leave a marked placeholder.

Companion skills: /vdataandmethods (before) · /vresults (after) · /vtable-format.
