---
name: wscheck
description: >-
  Munkakörnyezet-ellenőrzés (workspace health check) az óra elején. Csak olvas: megnézi, hogy fut-e az
  ágens, megvan-e a git és a gh (bejelentkezve), a mappa git-repó-e privát GitHub-távolival és tiszta
  állapottal, van-e házirend (CLAUDE.md / AGENTS.md / GEMINI.md), kizárja-e a .gitignore a .env-et, a
  kulcsokat és a data/ mappát, nincs-e titoknak látszó fájl a repóban, van-e Python, saját skill vagy
  workflow, helyi modell (ollama) és elég szabad hely. 🟢/🟡/🔴 táblázatot ad, minden sorhoz a javítással.
  Use when the user says "wscheck", "/wscheck", "munkakörnyezet-ellenőrzés", "ellenőrizd a
  munkakörnyezetemet", "workspace check", "is my setup OK".
---

# wscheck — munkakörnyezet-ellenőrzés

**Cél:** az óra (vagy bármely munkamenet) elején öt perc alatt kiderül, rendben van-e a munkakörnyezet.

## Szabályok (mindig)

- **Csak olvasol.** Ez a skill semmit nem telepít, nem ír át, nem commitol, nem töröl. Javítani csak akkor
  javítasz, ha a felhasználó a táblázat után kifejezetten kéri, és akkor is lépésenként, előbb megmutatva a parancsot.
- **Titkot soha nem nyitsz meg és nem írsz ki.** Gyanús fájlnak csak a NEVÉT mondod. `.env`, kulcs- vagy
  jelszófájl tartalmát ne olvasd be, ne idézd.
- Jelszót, tokent, kétlépcsős kódot a felhasználó maga ír be; te csak megmondod, melyik parancsot futtassa.

## Lépések

1. **Melyik mappa?** A felhasználó projekt- vagy skill-repójának mappája (ahol az ágenst indította). Ha nem
   egyértelmű, kérdezd meg egyetlen kérdéssel.
2. **Futtasd az ellenőrzést** ebből a skillmappából (a `scripts/` mappa a SKILL.md mellett van):
   - macOS / Linux: `bash <skillmappa>/scripts/check.sh "<projektmappa>"`
     (Claude Code-ban a skillmappa: `${CLAUDE_SKILL_DIR}`)
   - Windows: `powershell -ExecutionPolicy Bypass -File "<skillmappa>\scripts\check.ps1" "<projektmappa>"`
   A szkript egy Markdown-táblázatot ír ki: 🟢 rendben · 🟡 működik, de érdemes javítani · 🔴 javítani kell.
3. **Add vissza a táblázatot változtatás nélkül**, alatta egy mondatban az összesítést.
4. **A 🔴 sorokra** írd le sorrendben, mit kell tenni (a táblázat „Javítás” oszlopa alapján, a felhasználó
   rendszerére szabva: macOS-en `brew`, Windowson `winget`). A zárójeles számok a kurzus 16 beállítási lépésére utalnak.
5. **Végül kérdezd meg:** „Javítsuk most a piros sorokat?” — és csak igen után kezdj bele, egyesével.

## Mit néz meg (11 sor)

| # | Ellenőrzés | 🔴 ha… |
|---|---|---|
| 1 | Ágens (Antigravity / Claude Code) | — (legfeljebb 🟡: ha a skill fut, az ágens is fut) |
| 2 | git + név/e-mail | nincs git |
| 3 | gh + bejelentkezés | nincs gh vagy nincs bejelentkezve |
| 4 | Git-repó, privát távoli, mentett állapot | nem repó / nincs origin / NYILVÁNOS repó |
| 5 | Házirend (CLAUDE.md · AGENTS.md · GEMINI.md) | egyik sincs, se a mappában, se globálisan |
| 6 | .gitignore | nem zárja ki a .env-et, a kulcsokat vagy a data/ mappát |
| 7 | Titkok a repóban | titoknak látszó fájlnév van a gitben (csak név!) |
| 8 | Python ≥ 3.10 | nincs Python |
| 9 | Saját skill / workflow | egy sincs (a wscheck nem számít) |
| 10 | Helyi modell (ollama) | — opcionális, legfeljebb 🟡 |
| 11 | Szabad hely | 5 GB alatt |

Ha a szkript nem fut (pl. Windowson tiltott a szkriptfuttatás), futtasd a fenti `-ExecutionPolicy Bypass`
formát; ha az sem megy, végezd el ugyanezeket a csak olvasó ellenőrzéseket egyenként, és ugyanilyen táblázatot adj.
