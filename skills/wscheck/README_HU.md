# wscheck — munkakörnyezet-ellenőrző skill

Egy kis skill, amely az óra elején megnézi, rendben van-e a munkakörnyezeted. **Csak olvas**: semmit nem
telepít, nem ír át, nem töröl. A végén 🟢/🟡/🔴 táblázatot kapsz, minden sor mellett a javítással.

A mappa tartalma:

```
wscheck/
├── SKILL.md            ← az ágensnek szóló leírás
├── README_HU.md        ← ez a fájl
└── scripts/
    ├── check.sh        ← macOS / Linux
    └── check.ps1       ← Windows (PowerShell)
```

## Telepítés — Google Antigravity

Az Antigravity a skilleket mappaként keresi; a mappa neve legyen `wscheck`, benne a `SKILL.md`.

- **Csak ebben a projektben:** másold a mappát a projekt gyökerébe így: `.agents/skills/wscheck/`
  (a régebbi `.agent/skills/` helyet is olvassa).
- **Minden projektben:** `~/.gemini/config/skills/wscheck/`
  (az IDE a régebbi `~/.gemini/antigravity/skills/` helyet is olvassa).

macOS (Terminál, a kicsomagolt `wscheck` mappa mellől):
```bash
mkdir -p ~/.gemini/config/skills && cp -R wscheck ~/.gemini/config/skills/
```
Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.gemini\config\skills" | Out-Null; Copy-Item -Recurse wscheck "$env:USERPROFILE\.gemini\config\skills\"
```
Indíts új beszélgetést. Az Antigravity 2.0-ban írd be: `/wscheck`; az IDE-ben kérd név szerint:
„Futtasd a wscheck skillt ebben a mappában.” A betöltött skilleket az ágens-panel **Customizations** menüjében látod.

## Telepítés — Claude Code

- **Minden projektben:** `~/.claude/skills/wscheck/`
- **Csak egy repóban (commitolható, így minden gépeden ott lesz):** `.claude/skills/wscheck/`

macOS:
```bash
mkdir -p ~/.claude/skills && cp -R wscheck ~/.claude/skills/
```
Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null; Copy-Item -Recurse wscheck "$env:USERPROFILE\.claude\skills\"
```
Indítsd újra a Claude Code-ot a projektmappádban, és írd be: `/wscheck`.

## Kézzel is futtatható

macOS: `bash ~/.claude/skills/wscheck/scripts/check.sh .` (vagy az Antigravity-mappából)
Windows: `powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\wscheck\scripts\check.ps1" .`

## Mit jelentenek a színek

🟢 rendben · 🟡 működik, de érdemes javítani · 🔴 ezt javítsd, mielőtt adatot gyűjtesz.
A javításoknál a zárójeles szám a kurzus 16 beállítási lépésére utal.

Források (2026. október 12.): https://antigravity.google/docs/skills · https://antigravity.google/docs/rules ·
https://code.claude.com/docs/en/skills
