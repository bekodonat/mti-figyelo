---
name: vcodebook
description: >-
  Write or audit a coding scheme (a codebook) before anything is labelled: the unit of observation, three
  to seven codes each with a one-line definition, an inclusion rule, a real example and a near miss, the
  decision rules for boundary cases, a set-aside code so every unit has a destination, and the hand-coding
  plan. Produces codebook.md in the project folder and changes no data. Use when the user says "codebook",
  "coding scheme", "write the codes", "define my categories", "what is my unit", or "/vcodebook". Always
  trigger when the user runs /vcodebook.
---

# vcodebook — the instrument before the measurement

A label is a measurement, and the codebook is the instrument that produces it. Agreement between you and a
machine, or between two people, means nothing until the unit and the rules are written down. This skill
writes `codebook.md` with you, or audits one you already have. It never touches the texts.

## Workflow

1. **Fix the unit of observation.** What is one row: a document, a paragraph, a sentence, a speech, a
   press release? Decide it before coding, never after, and write it as the first line. If you cannot say
   what one row is, the analysis has not started.
2. **Name the codes.** Three to seven for a first scheme. Together they must cover every unit (exhaustive)
   and rarely compete for the same unit (near-exclusive). For each code write four lines:
   - *Definition*: one sentence, in words a stranger would apply the same way.
   - *Inclusion rule*: what has to be present for the code to apply.
   - *Example*: a verbatim passage from your own texts that earns the code.
   - *Near miss*: a passage that looks like it but does not qualify, and why.
3. **Write the decision rules.** When two codes compete for one unit: which wins, or is the unit coded by
   its dominant part, or set aside? When a unit is mixed, empty, off-topic or unreadable? A rule written
   now saves an argument per unit later.
4. **Add the set-aside code.** "None of these" and "cannot be coded" are codes too. Every unit then has a
   destination, and the count check later is simple: units in = units coded + units set aside.
5. **Pull the hard cases first.** Before freezing the scheme, read five to ten units that are genuinely
   hard for the construct and run them through the rules. A scheme that only works on easy cases is not
   finished.
6. **Write the hand-coding plan.** How many units you will code yourself before trusting a machine (20
   to 30 for a first check, a hundred or more for a paper), who codes, and that the hand coding happens
   blind to the machine's labels.
7. **Version it.** `codebook.md` carries a version and a date. Every later change is a new version, because
   a changed codebook is a different instrument: labels made under v1 and v2 cannot be pooled, and
   agreement is re-checked after each change on a fresh sample.

## The file

```markdown
# Codebook — <project> · v1 · <date>
Unit of observation: one <document / paragraph / sentence>.
Set-aside code: NONE (no code applies) · UNREADABLE (cannot be coded).

## Codes
### 1 <CODE NAME>
Definition: ...
Include when: ...
Example: "..." (file, line)
Near miss: "..." — not this code because ...

## Decision rules
- Two codes compete: ...
- Mixed unit: ...
- Empty or off-topic unit: NONE.

## Hand-coding plan
Units: 30 · coder: <name> · blind to machine labels · sample: random, seed 1.
```

## Output

`codebook.md` in the project folder, written only when asked. In audit mode, a table with one row per code
(definition present, example real, near miss present, rule covered) and the list of gaps.

## Rules

- The definitions are yours. The model may propose wording and pull candidate examples; it does not decide
  what a category means.
- Every example is a real passage from your texts, with its location. An invented example is not an example.
- A code without a near miss is a wish, not a code.
- Never change a definition silently after labels exist. New version, new date, re-check.
- Keep the scheme small. A category you cannot hand-code reliably yourself will not be coded reliably by
  a machine either.

Companion skills: /vclassify (apply the codebook), /vcoder-agreement (check the labels against you),
/vstudydesign (the question the codes serve).
