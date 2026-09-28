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
