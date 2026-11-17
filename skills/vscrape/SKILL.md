---
name: vscrape
description: >-
  VSCRAPE (vanilla scraping workflow): the shareable, agent-neutral, lab-free recipe for collecting text at
  scale into a coded table cheaply with an AI coding agent: define done, parse with plain code, fetch once,
  pick the model on 30 hand-checked pages, extract in batch with a cached prefix, escalate only
  disagreements, verify and log cost. Ships three standard-library scripts (fetch.py, check_complete.py,
  cost.py). Worked example: scraping legal or legislative amendments. Use ONLY when the user asks for
  vscrape or the vanilla/generic/shareable scraping workflow: "/vscrape", "vanilla scrape", "the cheap
  scraping workflow", "scrape amendments into a table cheaply", "how do I collect text at scale with an
  agent". Always trigger when the user runs /vscrape.
---

# vscrape — collect text at scale, cheaply (vanilla)

A reusable workflow for turning many pages or documents into one coded table. Running example: every
amendment to a set of constitutions or statutes, one row per amendment, from official sites, archives
and scanned compilations. Replace "amendment" and "jurisdiction" with your own item and group.

## The idea

**Agents decide; code does the work.** An agent that reads 50 pages pays for the same tokens 50 times,
plus everything it re-reads on every turn. Anthropic's own measurements: an agent uses about 4 times the
tokens of a chat, and several agents together about 15 times. That multiplier is worth paying for
judgement, parallel exploration or very large context. Scraping and extraction need almost none of it.
Let the agent *write* a script once; the script then does the repetitive work for nothing. The
expensive model judges only what is left.

## Workflow

### Step 1: Define done, before touching a page
Write down (a) the schema: one row per item, fixed fields, allowed values; and (b) the completeness test:
for every group (jurisdiction, year, court), `rows captured + rows explained = the official count`, taken
from an official tally. "Explained" means an item you know exists but could not extract, each with a
written reason (repealed, never published, scan unreadable). Without this test you cannot tell a finished
scrape from a truncated one: a tidy table can be a fifth short and nothing errors.

### Step 2: Parse first with plain code
Tables, section markers, numbered lists, repeated headers and official indexes need no AI. Ask the agent
to write a parser (regex or an HTML parser), run it, and look at what it could *not* classify. Only that
residue needs a model. This step often removes most of the volume.

### Step 3: Fetch once
```bash
python3 scripts/fetch.py urls.txt --out data              # 1 request per second per host
python3 scripts/fetch.py urls.txt --out data --rate 2     # slower for a fragile server
python3 scripts/fetch.py urls.txt --out data --resample-404 0.2
```
Download every page once, slowly, and keep the raw file; all later work reads the files, never the
website. The script is resumable (re-run the same command), retries 429 and 5xx errors with back-off,
and writes `data/manifest.csv` (url, saved path, HTTP status, SHA-1, UTC time). Respect each site's
terms and robots rules and identify yourself with `--user-agent`. A burst of 404s can be a server
shedding load, so before you record any gap as real, run `--resample-404` and check that the sample
still 404s.

### Step 4: Pick the model on about 30 pages you checked by hand
Hand-code 30 pages that cover the awkward cases (old scans, odd layouts, two languages). Run the same
prompt on a small, a medium and a large model at low effort. Keep the cheapest model that gets them
right. Compare cost per *finished row*, not per request: a cheap model that needs reruns is not cheap.
Check the outputs for agreement between models on the same page; two "different" runs that agree on
every row may be one server answering twice.

### Step 5: Extract the rest in batch, with a cached prefix
Use the provider's batch interface (about half price, results within a day) for work nobody is waiting
on. Build every request the same way: **stable instructions first** (codebook, JSON schema, three worked
examples), then the page text last. The stable prefix is read from the cache at a fraction of the input
price. Ask for a fixed JSON schema, key each result by the file's SHA-1, and expect results back in any
order. Estimate first:
```bash
python3 scripts/cost.py --items 12000 --in-tokens 650 --out-tokens 150 --prefix-tokens 1500 --escalate 0.05
```

### Step 6: Escalate only the disagreements
Run the cheap model twice (or two cheap models) and send only the rows where they disagree, or where a
field fails validation, to the large model or to a person. Typically a few per cent of rows.

### Step 7: Verify, and log cost per stage
```bash
python3 scripts/check_complete.py rows.csv expected.csv --group-col jurisdiction --id-col amendment_id
```
It prints, per group, captured + explained against the official count and exits non-zero on any gap.
Then read 20 rows by eye against their source pages, chosen at random, including some from the smallest
groups. Finally record, per stage, tokens in, tokens written, cache reads and dollars. The next scrape
is then budgeted from real numbers, not from this guide.

## Prices (planning estimates)
Anthropic first-party list prices, cached September 25, 2026, per million tokens in / out: Haiku 4.5
$1 / $5, Sonnet 5.5 $2 / $10, Opus 5.5 $4 / $20. Batch: minus 50%. Cache reads: 0.1 times the input
price (0.05 times on Opus 5.5); writing the cache costs more (1.25 times for the 5-minute cache). **Check
the live pricing page before you budget.** A token is roughly three-quarters of a word.

Four ways to pay for the same table (about 8 million tokens, planning estimates, not measurements):
an agent reads every page, $150 to $600; a large model, one call per page, about $75; a medium model in
batch with reused instructions, about $15; parse first, then batch, then escalate, about $5 to $10.

## Running it with agents cheaply
- **The orchestrator plans and writes the scripts.** Use your strongest model for the plan, the parser
  and the schema, and for the judgement calls in Step 6. It should not read the pages itself.
- **Subagents run on a cheaper model, each with a written brief:** the goal, the output file path and
  format, the sources allowed, a search budget, and what *not* to do. "Look into the southern states" is
  not a brief.
- **Agents write files as they go**, one record at a time, so a crash or usage limit costs only the item
  in flight. A usage limit kills the final reply, not what was already written: check the files before
  relaunching an agent.
- **One shared web-search cap.** Web-search limits are usually per session and shared by the parent and
  every subagent. Give each brief its own search budget and switch to fetching known URLs.
- **Match effort to the task.** One agent with a few tool calls for a fact lookup; two to four subagents
  for a comparison; many only for broad research with clearly divided scope. A scrape with known URLs is
  not broad research.

## Output format
Report to the user: the schema; per-group reconciliation (the `check_complete.py` table); which model
was chosen on the 30-page test and why; the cost per stage against the estimate; the rows escalated and
how they were resolved; and every group that does not reconcile, with the reason.

## Rules
- Don't let an agent read every page when a script can. Don't fetch a page twice. Don't call a table
  finished until `check_complete.py` exits 0.
- Don't treat a clean-looking row count as completeness. Don't record a 404 as a gap before re-probing.
- Don't guess a missing field: leave it empty and say why. Don't invent items to make a count reconcile.
- Don't publish scraped text you may not redistribute; share the schema, the code and the extracted
  fields instead.

## Scripts
`scripts/fetch.py`, `scripts/check_complete.py`, `scripts/cost.py`: Python 3.9+, standard library only.
Run any with `--help`.
