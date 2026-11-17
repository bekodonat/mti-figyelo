---
name: workplace-setup
description: A workspace skill for coding agents on macOS, Linux and Windows. Checks and sets up the workspace environment.
---

# workplace-setup (vanilla)

A workspace skill for coding agents that checks and sets up a workspace on macOS, Linux or Windows.

## Wizard — scan first, then fix only the gaps (START HERE)

1. **Scan (read-only, always first):**
   ```bash
   bash skills/workplace-setup/scripts/scan.sh
   ```
   Each row is:
   - `✓` present
   - `⚠` present but needs attention
   - `✗` missing, with the fix next to it

2. **Fix each ✗ / ⚠ in dependency order:**
   Package manager → git → Node → the agent CLI → Python → optional tools.
   Propose the command, run it if the user agrees, move on. Don't install optional tools the user has no use for.

3. **Things only the user can do (logins, passwords, 2FA):**
   Print the exact command and wait. Never type a password, token or key for them.

4. **Re-scan and report the result in one short table.**

## 1. Toolchain — three tiers

| Tier | Tool | Why |
| :--- | :--- | :--- |
| **Required** | `git` | Version control: every change is saved and reversible |
| **Required** | Coding agent CLI | The agent itself |
| **Recommended** | GitHub account + `gh` | Private repo for your skills; `gh auth login` |
| **Recommended** | Python 3.11+ in a virtual environment | Data work without breaking system Python |
| **Recommended** | Node.js LTS | Needed to install agent CLIs via npm |
| **Optional** | `pandoc` | Convert Markdown ↔ Word ↔ HTML ↔ LaTeX |
| **Optional** | `poppler` (`pdftoppm`, `pdfinfo`) | Turn PDF pages into images |
| **Optional** | `ImageMagick` (`magick`) | Resize and convert images |
| **Optional** | `LibreOffice` (`soffice`) | Word/Excel → PDF without Office |
| **Optional** | `Ollama` | Run open-weight models locally |

## 2. How the agent reports back (house rules)

These apply in every session once this skill is loaded. Adjust them in `config.md`.

1. **Outcome first.** Open with one or two sentences: what happened and what it means.
2. **Number every choice (1. 2. 3.)** so the user can reply with a digit. Use letters (A, B, C) for section labels, never digits.
3. **One question at a time.** Never a list of ten questions.
4. **Explain the jargon once, inline:** `git push` (= upload your saved changes to GitHub). Keep the term; add the gloss.
5. **No needless pauses.** In a multi-step setup, propose the sensible default and proceed; stop only for things that are destructive, cost money, or need credentials.
6. **Short and scannable.** Tables small enough to fit a terminal (about 4 columns); no walls of text.
7. **Link what changed.** If the result is visible somewhere, give the link or path.
8. **Say what's verified and what isn't.** "Done and checked" vs "done, not tested".
9. **End with what's next:** either "working, ETA …", "done here", or numbered decisions for the user.

## 3. Your skills live in git (so they follow you)

Skills are folders under `skills/<name>/SKILL.md`. Put that folder under version control.

## 4. Moving work to another machine

1. On machine A: commit and push the project, write a note of where things stand.
2. On machine B: git pull, open agent in project, point it at the note.

## 5. Where output goes, and how it is named

- Deliverables (PDF, Word, figures, exports) go to the output folder in `config.md` (default: `./output/`).
- Version filenames: `<name>_<YYYYMMDD>_v<N>.<ext>` → `report_20261005_v2.pdf`. Never overwrite v1 with v2.
- Scratch files go in a temporary folder.

## 6. Secrets

- API keys, passwords and tokens never go into chat, skills, commits or filenames.
- Keep them in environment variables or `.env`.

## 7. Render toolkit

```bash
pdftoppm -png -r 100 out.pdf page # PDF -> page-1.png, page-2.png
pandoc in.md -o out.docx          # Markdown -> Word
soffice --headless --convert-to pdf in.docx # Word -> PDF
magick in.png -resize 1200x out.jpg # resize image
```

## 8. Long runs

1. Keep scripts in a normal project folder.
2. Make it resumable.
3. Retry network calls with backoff.
4. Keep machine awake (`caffeinate -ims <command>`).

## 9. Local models (optional)

Run open-weight models with Ollama (`ollama pull <model>`, `ollama run <model>`). Start server with `OLLAMA_CONTEXT_LENGTH=65536 ollama serve` for agent context.

## 10. Connectors (MCP)

Connectors let the agent use other apps (Google Drive, Slack, browser, GitHub). Add only what you need.
