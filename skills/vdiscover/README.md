# vdiscover: candidate themes from a corpus, before the codebook

A skill for coding agents (the open SKILL.md format). Run `/vdiscover` on a folder of texts when you do not
yet know your categories: it holds out 30 percent of the documents, clusters the rest (an embedding topic
model, or the bundled no-install TF-IDF script), picks the number of topics by a stated rule, lists each
topic's top terms and representative documents, flags the outliers to read, and hands the surviving themes
to `/vcodebook` as candidate codes. The scheme is then checked with `/vclassify` and `/vcoder-agreement` on
the held-out documents, never on the ones that produced it.

`scripts/discover_lite.py FOLDER [--kmin 3 --kmax 10] [--holdout 0.3] [--seed 1] [--out DIR]` needs only
Python 3.9 or newer; `--help` and `--selftest` answer.
