---
name: diagnostics
description: Comprehensive deep technical & logical diagnostics, pragmatic code simplification, and inspiring feature ideation. Trigger on /diagnostics, /diag, /doctor, $diagnostics or audit requests.
---

# Diagnostics Skill (Deep Technical, Logical & Creative Engineering Audit)

A universal diagnostic skill for coding agents. It performs an exhaustive, zero-compromise audit of system health, code logic, error resilience, and task execution, combined with an inspiring, creative engineering roadmap.

---

## ⚡ Quick Start & Execution Flow

Whenever triggered via `/diagnostics`, `/diag`, `/doctor`, `$diagnostics`, or upon user request:

### Step 1: Project Memory & Context Scan (Silent)
1. Check git log (`git log -n 10 --oneline`), status, existing documentation, `AGENTS.md`, and recent conversation context.
2. Identify:
   - What is the program's intended task and core mission?
   - What architectural decisions have already been made?
   - What ideas or approaches were previously considered and discarded? (Do **NOT** blindly re-propose discarded features unless justified with new context).

### Step 2: Automated Scanner Execution
Run the universal diagnostic scanner:
```bash
python3 skills/diagnostics/scripts/scan.py
```
Parse the JSON output for secrets, silent exception handlers, syntax errors, and stack footprint.

### Step 3: Deep Cognitive & Functional Audit (Core 1)
Evaluate the codebase strictly on **functional excellence and task execution** (do not focus on business value or marketing metrics):
* **Data Flow Integrity:** Do outputs of upstream functions precisely match expected inputs downstream?
* **State Machine & Lifecycle Safety:** Are there deadlocks, hanging promises, unclosed resources, or states that fail to recover on error?
* **Silent Errors & Resilience:** Are exceptions swallowed (`except: pass` / empty catches)? Are network timeouts, retries, and rate limits handled?
* **Pragmatic Simplicity:** Can complex or repetitive code be simplified cleanly without forcing unnecessary rewrites?

### Step 4: Creative & Inspiring Engineering Roadmap (Core 2)
* **Feature Supercharge:** Review each feature: how does it work, what makes it fragile, and how can it execute its task more solidly and smoothly?
* **Inspiring Feature Roadmap:**
  - **Quick Wins:** High-impact additions implementable in minutes (progress bars, better logging, export formats).
  - **Pro Capabilities:** Concurrency, caching, deduplication, auto-recovery.
  - **Visionary Extensions:** Smart format detection, interactive CLI/TUI, automated reporting or notifications.

---

## 📋 Response Format (Directly in Chat)

Always provide the diagnostic report **directly in the chat conversation** in the user's language (default: **Hungarian**), structured as follows:

```markdown
# 🩺 Rendszer- és Kód-Diagnosztika: [Projekt / Modul Neve]

### 🎯 1. Funkcionális Állapot & Feladatellátási Profil
- **Cél & Működés:** 1-2 mondatos összegzés a program feladatáról és aktuális megbízhatóságáról.
- **Megvalósítási Hatékonyság:** Mennyire stabilan és gyorsan látja el a feladatát.

---

### 🔬 2. Mély Diagnosztikai Eredmények (Technikai & Logikai Röntgen)
- 🔴 **Kritikus / Blokkerek:** (Syntax hiba, hardkódolt secret, logikai szakadás, csendes elhalálozás)
- 🟡 **Kockázatok & Peremfeltételek:** (Hiányzó timeout, lezáratlan erőforrás, formátum-érzékenység)
- 🟢 **Rendben lévő területek:** (Erősségek, stabil pontok)

---

### 🧹 3. Megfontolt Kódegyszerűsítés & Tisztítás (Pragmatic Refactor)
- Konkrét, indokolt javaslatok a kód tisztábbá, átláthatóbbá tételére (csak ott, ahol valóban javítja az érthetőséget vagy csökkenti a hibalehetőségeket).

---

### 💡 4. Inspiráló Funkció- és Fejlesztési Roadmap
- 🟢 **Gyors Nyereségek (Quick Wins):** 
- 🔵 **Pro Funkciók (Next-Level Capabilities):**
- 🟣 **Jövőbe mutató / Kreatív Irányok:**

---

### 🎯 5. Következő Lépések (Válassz egyet):
1. **[Azonnali javítás]:** A kritikus és sárga jelzésű technikai/logikai hibák automatikus javítása.
2. **[Funkcióbővítés]:** Egy kiválasztott Roadmap funkció implementálása.
3. **[Kódtisztítás]:** Az átláthatóságot javító egyszerűsítések elvégzése.
```
