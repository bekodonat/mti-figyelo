#!/usr/bin/env bash
# wscheck — munkakörnyezet-ellenőrzés (macOS / Linux). CSAK OLVAS: semmit nem ír, nem telepít, nem töröl.
# Használat:  bash scripts/check.sh [projektmappa]     (alapértelmezés: az aktuális mappa)
# Kimenet: Markdown-táblázat, soronként 🟢 rendben · 🟡 működik, de javítsd · 🔴 javítani kell.

DIR="${1:-$PWD}"
if [ ! -d "$DIR" ]; then echo "Nincs ilyen mappa: $DIR"; exit 2; fi
cd "$DIR" || exit 2

G="🟢"; Y="🟡"; R="🔴"
NG=0; NY=0; NR=0
echo "| | Ellenőrzés | Mit találtam | Javítás |"
echo "|---|---|---|---|"
row() { # $1 jel, $2 ellenőrzés, $3 részlet, $4 javítás
  case "$1" in "$G") NG=$((NG+1));; "$Y") NY=$((NY+1));; "$R") NR=$((NR+1));; esac
  printf '| %s | %s | %s | %s |\n' "$1" "$2" "$3" "${4:--}"
}
have() { command -v "$1" >/dev/null 2>&1; }

# 1. Ágens (Antigravity vagy Claude Code)
AG=""
for a in "/Applications/Antigravity.app" "$HOME/Applications/Antigravity.app"; do [ -d "$a" ] && AG="Antigravity"; done
have claude && AG="${AG:+$AG + }Claude Code ($(claude --version 2>/dev/null | awk "NR==1{print \$1}"))"
if [ -n "$AG" ]; then row "$G" "Ágens" "$AG" ""
else row "$Y" "Ágens" "nem találtam Antigravity-appot vagy claude parancsot" "ha az ágens fut, ez a sor nyugodtan sárga maradhat; különben 7. lépés"; fi

# 2. git + identitás
if have git; then
  GN=$(git config --global user.name 2>/dev/null); GE=$(git config --global user.email 2>/dev/null)
  if [ -n "$GN" ] && [ -n "$GE" ]; then row "$G" "git" "$(git --version | awk '{print $3}'), név és e-mail beállítva" ""
  else row "$Y" "git" "$(git --version | awk '{print $3}'), de nincs név/e-mail" 'git config --global user.name "Név"; git config --global user.email "a GitHub-e-mailed"'; fi
else row "$R" "git" "nincs telepítve" "brew install git (4. lépés)"; fi

# 3. gh + bejelentkezés
GHOK=0
if have gh; then
  if gh auth status >/dev/null 2>&1; then GHOK=1; row "$G" "gh (GitHub CLI)" "telepítve, be vagy jelentkezve" ""
  else row "$R" "gh (GitHub CLI)" "telepítve, de nem vagy bejelentkezve" "gh auth login (6. lépés)"; fi
else row "$R" "gh (GitHub CLI)" "nincs telepítve" "brew install gh (4. lépés)"; fi

# 4. git-repó, privát távoli, tiszta állapot
INREPO=0
if have git && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  INREPO=1; ROOT=$(git rev-parse --show-toplevel)
  row "$G" "Git-repó" "a mappa repó: $(basename "$ROOT")" ""
  URL=$(git remote get-url origin 2>/dev/null)
  if [ -z "$URL" ]; then row "$R" "Távoli repó" "nincs origin" "gh repo create <név> --private --source . --push (9. lépés)"
  elif [ "$GHOK" = 1 ] && echo "$URL" | grep -q "github.com"; then
    VIS=$(gh repo view "$URL" --json visibility --jq .visibility 2>/dev/null)
    case "$VIS" in
      PRIVATE) row "$G" "Távoli repó" "GitHub, privát" "";;
      PUBLIC)  row "$R" "Távoli repó" "GitHub, NYILVÁNOS" "gh repo edit --visibility private --accept-visibility-change-consequences";;
      *)       row "$Y" "Távoli repó" "GitHub, a láthatóság nem kérdezhető le" "gh repo view --web, és nézd meg a Settings oldalon";;
    esac
  else row "$Y" "Távoli repó" "van origin, de a láthatóság nem ellenőrizhető" "jelentkezz be a gh-val, és futtasd újra"; fi
  NCH=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  AHEAD=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo "?")
  if [ "$NCH" = 0 ] && [ "$AHEAD" = 0 ]; then row "$G" "Mentett állapot" "nincs commitolatlan vagy pusholatlan változás" ""
  elif [ "$NCH" = 0 ] && [ "$AHEAD" = "?" ]; then row "$Y" "Mentett állapot" "tiszta, de nincs követett távoli ág" "git push -u origin HEAD"
  else row "$Y" "Mentett állapot" "$NCH változott fájl, $AHEAD pusholatlan commit" 'git add -A; git commit -m "..."; git push (15. lépés)'; fi
else
  row "$R" "Git-repó" "ez a mappa nem git-repó" "git init, vagy nyisd meg a skill-repód mappáját (9–10. lépés)"
fi

# 5. Házirend
HR=""
for f in CLAUDE.md AGENTS.md GEMINI.md .agents/rules .agent/rules; do [ -e "$f" ] && HR="$HR $f"; done
GHR=""
for f in "$HOME/.claude/CLAUDE.md" "$HOME/.gemini/GEMINI.md" "$HOME/.gemini/AGENTS.md" "$HOME/.gemini/config/GEMINI.md" "$HOME/.gemini/config/AGENTS.md"; do [ -e "$f" ] && GHR="$GHR ${f/#$HOME/~}"; done
if [ -n "$HR" ]; then row "$G" "Házirend" "a mappában:$HR" ""
elif [ -n "$GHR" ]; then row "$Y" "Házirend" "csak globális:$GHR" "tegyél CLAUDE.md-t (Claude Code) vagy AGENTS.md/GEMINI.md-t (Antigravity) a repóba (11. lépés)"
else row "$R" "Házirend" "nincs CLAUDE.md / AGENTS.md / GEMINI.md" "írd meg a repóba (11. lépés)"; fi

# 6. .gitignore lefedettség
if [ "$INREPO" = 1 ]; then
  MISS=""
  for p in ".env" "kulcs.pem" "kulcs.key" "id_rsa" "data/minta.csv"; do
    git check-ignore -q --no-index "$p" 2>/dev/null || MISS="$MISS $p"
  done
  if [ -z "$MISS" ]; then row "$G" ".gitignore" ".env, kulcsok és data/ kizárva" ""
  else row "$R" ".gitignore" "nincs kizárva:$MISS" "írd a .gitignore-ba: .env, *.pem, *.key, id_rsa*, data/ (12. lépés)"; fi
fi

# 7. Titoknak látszó követett fájl (csak fájlnév, tartalom soha)
if [ "$INREPO" = 1 ]; then
  SUS=$(git ls-files 2>/dev/null | grep -Ei '(^|/)\.env($|\.)|\.pem$|\.key$|\.p12$|\.pfx$|(^|/)id_(rsa|ed25519|ecdsa)|credential|secret|token|service[-_]?account.*\.json$|(^|/)\.netrc$' | grep -Eiv '\.env\.(example|sample|template)$|(^|/)(SKILL|README)[^/]*\.md$' | head -10)
  if [ -z "$SUS" ]; then row "$G" "Titkok a repóban" "nincs titoknak látszó fájlnév" ""
  else row "$R" "Titkok a repóban" "gyanús: $(echo "$SUS" | tr '\n' ' ')" "git rm --cached <fájl>, tedd a .gitignore-ba, és cseréld le a kulcsot (12. lépés)"; fi
fi

# 8. Python
PY=""; for p in python3 python; do have "$p" && { PY=$p; break; }; done
if [ -n "$PY" ]; then
  V=$($PY -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)
  if $PY -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then row "$G" "Python" "$PY $V" ""
  else row "$Y" "Python" "$PY $V (régi)" "brew install python (5. lépés)"; fi
else row "$R" "Python" "nincs" "brew install python (5. lépés)"; fi

# 9. Saját skill / workflow (a wscheck nem számít)
CNT=0; WHERE=""
for d in "$HOME/.claude/skills" ".claude/skills" ".agents/skills" ".agent/skills" "$HOME/.gemini/config/skills" "$HOME/.gemini/antigravity/skills" "$HOME/.gemini/antigravity-cli/skills"; do
  [ -d "$d" ] || continue
  n=$(find "$d" -maxdepth 2 -name SKILL.md -not -path "*/wscheck/*" 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" -gt 0 ] && { CNT=$((CNT+n)); WHERE="$WHERE ${d/#$HOME/~}($n)"; }
done
for d in ".agents/workflows" ".agent/workflows"; do
  [ -d "$d" ] || continue
  n=$(find "$d" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" -gt 0 ] && { CNT=$((CNT+n)); WHERE="$WHERE $d($n)"; }
done
if [ "$CNT" -gt 0 ]; then row "$G" "Saját skill/workflow" "$CNT db:$WHERE" ""
else row "$R" "Saját skill/workflow" "egy sincs (a wscheck nem számít)" "írd meg az elsőt (14. lépés)"; fi

# 10. Helyi modell (opcionális)
if have ollama; then row "$G" "Helyi modell (opcionális)" "ollama telepítve" ""
else row "$Y" "Helyi modell (opcionális)" "nincs ollama" "nem kötelező; érzékeny adathoz: brew install ollama"; fi

# 11. Szabad hely
FREEKB=$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "$FREEKB" ]; then
  GB=$((FREEKB/1024/1024))
  if [ "$GB" -ge 20 ]; then row "$G" "Szabad hely" "$GB GB" ""
  elif [ "$GB" -ge 5 ]; then row "$Y" "Szabad hely" "$GB GB" "korpuszhoz kevés lehet; takaríts"
  else row "$R" "Szabad hely" "$GB GB" "szabadíts fel helyet, mielőtt adatot gyűjtesz"; fi
fi

echo
echo "Összesen: $G $NG · $Y $NY · $R $NR"
