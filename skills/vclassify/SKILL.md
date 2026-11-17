---
name: vclassify
description: >-
  Apply your codebook to every document with a language model and get one table back: labels.csv with one
  row per file, the code, a one-line reason and the sentence that earned it. Fixed answer fields, the
  model and prompt pinned and logged in models.md, a count check (files in = rows coded + rows set aside)
  and a sentence check (every quoted sentence occurs in its file), both run by label_check.py. Use when
  the user says "label my files", "classify with my codebook", "code every document", "apply the
  codebook", or "/vclassify". Always trigger when the user runs /vclassify.
---

# vclassify — your codebook, applied to every document, checkably

Your scheme, not the model's. Every label is tied to the words that earned it, so a label you cannot
justify from the sentence is a label you do not have. The output is one table a person can read against
the files, and a log that says exactly which instrument produced it.

## Inputs

- `codebook.md` from /vcodebook (unit, codes, rules, set-aside code).
- A folder of text files, one file per unit, plain text, UTF-8.

## Workflow

1. **Freeze the instructions.** The prompt is the codebook plus the answer format: exactly one code from
   the list (or the set-aside code), a reason of at most twenty words, and one sentence copied verbatim
   from the file. Save it as `prompt.md` with a version and a date. Do not improvise the instructions per
   file.
2. **Pin and log the model.** Write `models.md`: the model's exact id or name and revision, the date, the
   prompt version, temperature and any other setting. The same prompt on a newer model is a different
   instrument, so a change here is a new run, not a continuation.
3. **Run twenty first.** Label twenty files and read every row against its file. If the reasons are vague
   or the sentences are paraphrased, fix the prompt (new version) before going further.
4. **Run the rest.** One row per file in `labels.csv`: `file, code, reason, sentence, model, prompt_version`.
   Files the model cannot code get the set-aside code and a reason, never a blank.
5. **Check mechanically.**
   ```bash
   python3 scripts/label_check.py labels.csv --folder texts --codes "A,B,C,NONE,UNREADABLE"
   ```
   It fails loudly when a file has no row or two rows, a code is not in the list, a quoted sentence does
   not occur in its file, or the count does not close (files in = coded + set aside).
6. **Disagree with one label.** Pick a row you doubt and ask the model to argue back from the codebook.
   If the codebook is unclear, fix the codebook (new version) and re-run; do not patch the label by hand.
7. **Hand to /vcoder-agreement** before you count anything. Machine labels are not data until they have
   been checked against your own coding of a sample.

## Where to run it

In the desktop app or the chat client for the codebook, the first twenty files and the demo. Through the
API with a script when there are more documents than one session holds, when the labels go into a paper
or a report (pin the model, re-run it), when the same instructions run on every document (batch and cached
instructions cut the price), when the texts are sensitive (you choose who serves them), or when you will
run it again next year. On your own machine with an open model (/vrun-local) when the texts cannot leave
the room.

## Output

`labels.csv`, `models.md`, `prompt.md`, and the check report: files in, rows coded, rows set aside,
failures listed by file.

## Rules

- One code per unit unless the codebook says otherwise; the model does not get to invent "both".
- The sentence is copied, never summarised. A reason is not evidence; the sentence is.
- No blank cells: a file the model cannot code is set aside with a reason.
- Never pool labels made under two prompt or model versions as if they were one run.
- The count must close before anything is counted.

Companion skills: /vcodebook (before), /vcoder-agreement (after), /vdatavalidation (the corpus before
any label), /vrun-local (the same job on your own machine).
