# vcoder-agreement: machine labels against your own hand coding

A skill for coding agents (the open SKILL.md format). You hand-code a sample from your codebook into
`hand.csv` (columns `file, code`), the agent runs

    python3 scripts/agreement.py hand.csv labels.csv --id file --code code

and reads the result with you: exact agreement, Cohen's kappa, per-category precision and recall with n
and base rate, the confusion matrix, every mismatch. Python 3.9+, standard library; `--selftest` checks
the kappa arithmetic on a textbook table.
