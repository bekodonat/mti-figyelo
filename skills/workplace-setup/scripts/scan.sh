#!/usr/bin/env bash
# workplace-setup scan — read-only. Reports what is present vs missing on this machine.
# Works on macOS, Linux, WSL and Git Bash. Installs nothing.
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
ok=0; warn=0; bad=0
P(){ printf " %s %-26s %s\n" "$1" "$2" "$3"; case "$1" in ✓)ok=$((ok+1));; ⚠)warn=$((warn+1));; ✗)bad=$((bad+1));; esac; }
have(){ command -v "$1" >/dev/null 2>&1; }
OS="$(uname -s 2>/dev/null)"
case "$OS" in
  Darwin) PLAT=mac; PM="brew install";;
  Linux) PLAT=linux; PM="sudo apt install"; grep -qi microsoft /proc/version 2>/dev/null && PLAT=wsl;;
  MINGW*|MSYS*|CYGWIN*) PLAT=win; PM="winget install";;
  *) PLAT=other; PM="<your package manager> install";;
esac
fix(){
  case "$PLAT" in
    mac) echo "brew install $1";;
    linux|wsl) echo "sudo apt install $2";;
    win) echo "winget install $3";;
    *) echo "install $1";;
  esac
}
echo "── machine ──"
P "✓" "OS" "$OS ($PLAT)"
P "✓" "user @ host" "$(whoami 2>/dev/null) @ $(hostname 2>/dev/null)"
if [ "$PLAT" = mac ]; then
  have brew && P "✓" "Homebrew" "$(brew --version 2>/dev/null | head -1)" || P "✗" "Homebrew" "see https://brew.sh"
fi
echo "── required ──"
have git && P "✓" "git" "$(git --version)" || P "✗" "git" "$(fix git git Git.Git)"
AGENT="${AGENT_CLI:-codex}"
if have "$AGENT"; then P "✓" "agent CLI ($AGENT)" "$($AGENT --version 2>/dev/null | head -1)"
elif have npm; then P "✗" "agent CLI ($AGENT)" "npm install -g @openai/codex"
else P "✗" "agent CLI ($AGENT)" "install Node first, then: npm install -g @openai/codex"; fi
if have git; then
  [ -n "$(git config --global user.name)" ] && [ -n "$(git config --global user.email)" ] \
  && P "✓" "git identity" "$(git config --global user.name)" \
  || P "⚠" "git identity" 'git config --global user.name "Your Name"; git config --global user.email you@example.org'
fi
echo "── recommended ──"
have node && P "✓" "Node.js" "$(node --version)" || P "✗" "Node.js" "$(fix node 'nodejs npm' OpenJS.NodeJS.LTS)"
if have gh; then
  gh auth status >/dev/null 2>&1 && P "✓" "GitHub CLI" "logged in" || P "⚠" "GitHub CLI" "gh auth login"
else P "✗" "GitHub CLI" "$(fix gh gh GitHub.cli)"; fi
PY=""; for c in python3 python py; do have "$c" && PY="$c" && break; done
if [ -n "$PY" ]; then
  V="$($PY -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)"
  if $PY -c 'import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)' 2>/dev/null; then
    P "✓" "Python" "$V ($(command -v $PY))"
  else
    P "⚠" "Python" "$V is old; want 3.11+ → $(fix python 'python3 python3-venv' Python.Python.3.12)"
  fi
  $PY -c 'import venv' 2>/dev/null && P "✓" "Python venv" "available" || P "⚠" "Python venv" "$(fix python python3-venv Python.Python.3.12)"
else
  P "✗" "Python" "$(fix python 'python3 python3-venv' Python.Python.3.12)"
fi
echo "── optional ──"
have pandoc && P "✓" "pandoc" "$(pandoc --version | head -1)" || P "✗" "pandoc" "$(fix pandoc pandoc JohnMacFarlane.Pandoc)"
have pdftoppm && P "✓" "poppler (pdftoppm)" "present" || P "✗" "poppler (pdftoppm)" "$(fix poppler poppler-utils oschwartz10612.Poppler)"
{ have magick || have convert; } && P "✓" "ImageMagick" "present" || P "✗" "ImageMagick" "$(fix imagemagick imagemagick ImageMagick.ImageMagick)"
{ have soffice || have libreoffice || [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; } \
&& P "✓" "LibreOffice" "present" || P "✗" "LibreOffice" "$(fix '--cask libreoffice' libreoffice TheDocumentFoundation.LibreOffice)"
have ollama && P "✓" "Ollama (local models)" "$(ollama --version 2>/dev/null | head -1)" || P "✗" "Ollama (local models)" "$(fix ollama 'see ollama.com/download' Ollama.Ollama)"
CH=""; for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"; do
  { have "$c" || [ -x "$c" ]; } && CH="$c" && break
done
[ -n "$CH" ] && P "✓" "headless browser" "$CH" || P "✗" "headless browser" "install Chrome, Chromium or Edge (HTML → PDF/PNG)"

echo "── agent skills ──"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
SK="${SKILLS_DIR:-$DIR/..}"
if [ -d "$SK" ]; then
  n=$(find "$SK" -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')
  P "✓" "skills folder" "$SK ($n skills)"
  if git -C "$SK" rev-parse >/dev/null 2>&1; then
    r=$(git -C "$SK" remote get-url origin 2>/dev/null)
    [ -n "$r" ] && P "✓" "skills in git" "remote set" || P "⚠" "skills in git" "no remote → gh repo create my-agent-skills --private --source $SK --push"
    [ -z "$(git -C "$SK" status --porcelain 2>/dev/null)" ] && P "✓" "skills committed" "clean" || P "⚠" "skills committed" "uncommitted edits → commit + push"
  else
    P "⚠" "skills in git" "not a repo → see SKILL.md §3"
  fi
else
  P "⚠" "skills folder" "missing → mkdir -p $SK"
fi
CFG="$DIR/config.md"
[ -f "$CFG" ] && P "✓" "config.md" "present" || P "⚠" "config.md" "copy config.example.md → config.md and fill it in"
case "$SK" in *Dropbox*|*OneDrive*|*iCloud*|*"Mobile Documents"*) P "⚠" "sync-folder check" "skills inside a cloud-sync folder: move them out";; esac
echo
echo "── summary: $ok ✓ · $warn ⚠ · $bad ✗ ──"
