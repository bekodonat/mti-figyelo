# wscheck - munkakornyezet-ellenorzes (Windows PowerShell 5.1+ / PowerShell 7). CSAK OLVAS: semmit nem ir, nem telepit, nem torol.
# Hasznalat:  powershell -ExecutionPolicy Bypass -File scripts\check.ps1 [projektmappa]
param([string]$Dir = (Get-Location).Path)
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
if (-not (Test-Path $Dir -PathType Container)) { Write-Output "Nincs ilyen mappa: $Dir"; exit 2 }
Set-Location $Dir
$G = [char]::ConvertFromUtf32(0x1F7E2); $Y = [char]::ConvertFromUtf32(0x1F7E1); $R = [char]::ConvertFromUtf32(0x1F534)
$script:N = @{ G = 0; Y = 0; R = 0 }
Write-Output "| | Ellenőrzés | Mit találtam | Javítás |"
Write-Output "|---|---|---|---|"
function Row($s, $c, $d, $f) {
  if ($s -eq $G) { $script:N.G++ } elseif ($s -eq $Y) { $script:N.Y++ } else { $script:N.R++ }
  if (-not $f) { $f = "-" }
  Write-Output "| $s | $c | $d | $f |"
}
function Have($n) { [bool](Get-Command $n -ErrorAction SilentlyContinue) }
$H = $env:USERPROFILE

# 1. Agens
$ag = @()
foreach ($p in @("$env:LOCALAPPDATA\Programs\Antigravity", "$env:ProgramFiles\Antigravity")) { if ($p -and (Test-Path $p)) { $ag += "Antigravity"; break } }
if (Have claude) { $v = (claude --version 2>$null | Select-Object -First 1); $ag += "Claude Code ($(($v -split ' ')[0]))" }
if ($ag.Count -gt 0) { Row $G "Ágens" ($ag -join " + ") "" }
else { Row $Y "Ágens" "nem találtam Antigravity-telepítést vagy claude parancsot" "ha az ágens fut, ez a sor nyugodtan sárga maradhat; különben 7. lépés" }

# 2. git + identitas
if (Have git) {
  $gv = ((git --version) -split ' ')[2]
  $gn = git config --global user.name 2>$null; $ge = git config --global user.email 2>$null
  if ($gn -and $ge) { Row $G "git" "$gv, név és e-mail beállítva" "" }
  else { Row $Y "git" "$gv, de nincs név/e-mail" 'git config --global user.name "Név"; git config --global user.email "a GitHub-e-mailed"' }
} else { Row $R "git" "nincs telepítve" "winget install Git.Git (4. lépés)" }

# 3. gh
$ghok = $false
if (Have gh) {
  gh auth status *> $null
  if ($LASTEXITCODE -eq 0) { $ghok = $true; Row $G "gh (GitHub CLI)" "telepítve, be vagy jelentkezve" "" }
  else { Row $R "gh (GitHub CLI)" "telepítve, de nem vagy bejelentkezve" "gh auth login (6. lépés)" }
} else { Row $R "gh (GitHub CLI)" "nincs telepítve" "winget install GitHub.cli (4. lépés)" }

# 4. repo, privat tavoli, tiszta allapot
$inrepo = $false
if (Have git) { $t = git rev-parse --is-inside-work-tree 2>$null; if ($t -eq "true") { $inrepo = $true } }
if ($inrepo) {
  $root = git rev-parse --show-toplevel
  Row $G "Git-repó" "a mappa repó: $(Split-Path $root -Leaf)" ""
  $url = git remote get-url origin 2>$null
  if (-not $url) { Row $R "Távoli repó" "nincs origin" "gh repo create <név> --private --source . --push (9. lépés)" }
  elseif ($ghok -and $url -match "github.com") {
    $vis = gh repo view $url --json visibility --jq .visibility 2>$null
    if ($vis -eq "PRIVATE") { Row $G "Távoli repó" "GitHub, privát" "" }
    elseif ($vis -eq "PUBLIC") { Row $R "Távoli repó" "GitHub, NYILVÁNOS" "gh repo edit --visibility private --accept-visibility-change-consequences" }
    else { Row $Y "Távoli repó" "GitHub, a láthatóság nem kérdezhető le" "gh repo view --web, és nézd meg a Settings oldalon" }
  } else { Row $Y "Távoli repó" "van origin, de a láthatóság nem ellenőrizhető" "jelentkezz be a gh-val, és futtasd újra" }
  $nch = @(git status --porcelain 2>$null).Count
  $ahead = git rev-list --count '@{u}..HEAD' 2>$null; if ($LASTEXITCODE -ne 0) { $ahead = "?" }
  if ($nch -eq 0 -and "$ahead" -eq "0") { Row $G "Mentett állapot" "nincs commitolatlan vagy pusholatlan változás" "" }
  elseif ($nch -eq 0 -and "$ahead" -eq "?") { Row $Y "Mentett állapot" "tiszta, de nincs követett távoli ág" "git push -u origin HEAD" }
  else { Row $Y "Mentett állapot" "$nch változott fájl, $ahead pusholatlan commit" 'git add -A; git commit -m "..."; git push (15. lépés)' }
} else { Row $R "Git-repó" "ez a mappa nem git-repó" "git init, vagy nyisd meg a skill-repód mappáját (9–10. lépés)" }

# 5. Hazirend
$hr = @(); foreach ($f in @("CLAUDE.md","AGENTS.md","GEMINI.md",".agents\rules",".agent\rules")) { if (Test-Path $f) { $hr += $f } }
$ghr = @(); foreach ($f in @("$H\.claude\CLAUDE.md","$H\.gemini\GEMINI.md","$H\.gemini\AGENTS.md","$H\.gemini\config\GEMINI.md","$H\.gemini\config\AGENTS.md")) { if (Test-Path $f) { $ghr += ($f -replace [regex]::Escape($H), "~") } }
if ($hr.Count -gt 0) { Row $G "Házirend" "a mappában: $($hr -join ', ')" "" }
elseif ($ghr.Count -gt 0) { Row $Y "Házirend" "csak globális: $($ghr -join ', ')" "tegyél CLAUDE.md-t (Claude Code) vagy AGENTS.md/GEMINI.md-t (Antigravity) a repóba (11. lépés)" }
else { Row $R "Házirend" "nincs CLAUDE.md / AGENTS.md / GEMINI.md" "írd meg a repóba (11. lépés)" }

# 6. .gitignore
if ($inrepo) {
  $miss = @()
  foreach ($p in @(".env","kulcs.pem","kulcs.key","id_rsa","data/minta.csv")) { git check-ignore -q --no-index $p 2>$null; if ($LASTEXITCODE -ne 0) { $miss += $p } }
  if ($miss.Count -eq 0) { Row $G ".gitignore" ".env, kulcsok és data/ kizárva" "" }
  else { Row $R ".gitignore" "nincs kizárva: $($miss -join ' ')" "írd a .gitignore-ba: .env, *.pem, *.key, id_rsa*, data/ (12. lépés)" }
}

# 7. Titoknak latszo kovetett fajl (csak fajlnev)
if ($inrepo) {
  $pat = '(^|/)\.env($|\.)|\.pem$|\.key$|\.p12$|\.pfx$|(^|/)id_(rsa|ed25519|ecdsa)|credential|secret|token|service[-_]?account.*\.json$|(^|/)\.netrc$'
  $sus = @(git ls-files 2>$null | Where-Object { $_ -match $pat -and $_ -notmatch '\.env\.(example|sample|template)$|(^|/)(SKILL|README)[^/]*\.md$' } | Select-Object -First 10)
  if ($sus.Count -eq 0) { Row $G "Titkok a repóban" "nincs titoknak látszó fájlnév" "" }
  else { Row $R "Titkok a repóban" "gyanús: $($sus -join ' ')" "git rm --cached <fájl>, tedd a .gitignore-ba, és cseréld le a kulcsot (12. lépés)" }
}

# 8. Python (a Microsoft Store alias nem szamit)
$py = $null
foreach ($c in @("py","python","python3")) {
  if (Have $c) { $v = & $c -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null; if ($LASTEXITCODE -eq 0 -and $v) { $py = $c; $pv = $v; break } }
}
if ($py) {
  $ok = & $py -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" 2>$null
  if ($LASTEXITCODE -eq 0) { Row $G "Python" "$py $pv" "" } else { Row $Y "Python" "$py $pv (régi)" "winget install Python.Python.3.12 (5. lépés)" }
} else { Row $R "Python" "nincs (vagy csak a Store-alias)" "winget install Python.Python.3.12 (5. lépés)" }

# 9. Sajat skill / workflow
$cnt = 0; $where = @()
foreach ($d in @("$H\.claude\skills",".claude\skills",".agents\skills",".agent\skills","$H\.gemini\config\skills","$H\.gemini\antigravity\skills","$H\.gemini\antigravity-cli\skills")) {
  if (-not (Test-Path $d)) { continue }
  $n = @(Get-ChildItem $d -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne "wscheck" -and (Test-Path (Join-Path $_.FullName "SKILL.md")) }).Count
  if ($n -gt 0) { $cnt += $n; $where += "$($d -replace [regex]::Escape($H), '~')($n)" }
}
foreach ($d in @(".agents\workflows",".agent\workflows")) {
  if (Test-Path $d) { $n = @(Get-ChildItem $d -Filter *.md -File -ErrorAction SilentlyContinue).Count; if ($n -gt 0) { $cnt += $n; $where += "$d($n)" } }
}
if ($cnt -gt 0) { Row $G "Saját skill/workflow" "$cnt db: $($where -join ' ')" "" }
else { Row $R "Saját skill/workflow" "egy sincs (a wscheck nem számít)" "írd meg az elsőt (14. lépés)" }

# 10. Helyi modell (opcionalis)
if (Have ollama) { Row $G "Helyi modell (opcionális)" "ollama telepítve" "" }
else { Row $Y "Helyi modell (opcionális)" "nincs ollama" "nem kötelező; érzékeny adathoz: winget install Ollama.Ollama" }

# 11. Szabad hely
try {
  $drv = (Get-Item $H).PSDrive
  $gb = [math]::Floor((Get-PSDrive $drv.Name).Free / 1GB)
  if ($gb -ge 20) { Row $G "Szabad hely" "$gb GB" "" }
  elseif ($gb -ge 5) { Row $Y "Szabad hely" "$gb GB" "korpuszhoz kevés lehet; takaríts" }
  else { Row $R "Szabad hely" "$gb GB" "szabadíts fel helyet, mielőtt adatot gyűjtesz" }
} catch {}

Write-Output ""
Write-Output "Összesen: $G $($script:N.G) · $Y $($script:N.Y) · $R $($script:N.R)"
