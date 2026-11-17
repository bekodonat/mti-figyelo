# Project Agents & Skills Guidelines

## Workplace Setup (/ws)
Whenever the user types `/ws`, `$ws`, `/workplace-setup` or asks to run workplace setup:
1. Load and execute the `workplace-setup` skill.
2. Run the scan script: `bash skills/workplace-setup/scripts/scan.sh`.
3. Report the result following the House Rules:
   - **Outcome first**: 1-2 sentences summarizing state.
   - **Table**: Scannable 4-column summary (Tier, ✓, ⚠, ✗).
   - **Numbered choices**: (1. 2. 3.) for user responses.
   - **Gloss jargon**: Explain terms inline.
   - **Done and checked** status confirmation.

## Diagnostics & Code Audit (/diagnostics, /diag, /doctor)
Whenever the user types `/diagnostics`, `$diagnostics`, `/diag`, `$diag`, `/doctor` or asks for a diagnostic/audit:
1. Load and execute the `diagnostics` skill (`skills/diagnostics/SKILL.md`).
2. Follow the 4-phase audit:
   - **Memory & History Scan**: Check git history and previous context to avoid proposing discarded ideas.
   - **Automated Scan**: Run `python3 skills/diagnostics/scripts/scan.py`.
   - **Functional & Logic Deep Dive**: Focus strictly on task execution, data flow integrity, edge cases, and silent failure prevention (no business/marketing fluff).
   - **Pragmatic Simplicity & Creative Roadmap**: Provide clean, project-appropriate simplifications and inspiring, actionable next-level features.
3. Report the result directly as text in the chat in Hungarian.
