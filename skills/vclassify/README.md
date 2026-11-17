# vclassify: apply your codebook to every document

A skill for coding agents (the open SKILL.md format). Given `codebook.md` and a folder of text files, the
agent labels every file into `labels.csv` (file, code, reason, the sentence that earned it) with the model
and prompt pinned in `models.md`. `scripts/label_check.py` (Python 3.9+, standard library) checks that every
file has one row, every code is allowed, every quoted sentence occurs in its file and the count closes:

    python3 scripts/label_check.py labels.csv --folder texts --codes "A,B,C,NONE"

Then run `/vcoder-agreement` on a hand-coded sample before counting anything.
