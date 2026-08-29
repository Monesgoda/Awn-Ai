# INSTALL — Step-by-step for people who never installed anything

> You do NOT need to know programming. Follow these steps **in order**.
> Total time: about 10–20 minutes. You only do this **once**.

---

## What you need (2 pieces of free software first)

| Needed | What it is | Where to get it |
|---|---|---|
| **Python** | The engine that runs the tool | https://python.org/downloads |
| **OpenCode** | The AI that answers you | installed automatically by step 3 below |

An **internet connection** is needed during this install. After install you can
use the tool with no internet if you use a local/offline AI model.

---

## Step 1 — Install Python  ✔

1. Go to **https://python.org/downloads** and download the latest version.
2. Run the downloaded file.
3. ⚠️ **VERY IMPORTANT:** on the first screen, tick the box that says
   **"Add python.exe to PATH"**, then click **Install Now**.
4. Wait until it finishes, then close the window.

## Step 2 — Put the tool folder somewhere  ✔

1. Download this project (GitHub → green **Code** button → **Download ZIP**).
2. **Right-click** the ZIP → **Extract All** → keep the extracted folder
   somewhere easy to find, e.g. `C:\StealthClip` or your Desktop.
   *(Move the folder where you want BEFORE continuing — the folder can't be
   moved after install without repeating this.)*

## Step 3 — Install the tool (one click)  ✔

1. Open the extracted folder.
2. **Double-click `setup.bat`**.
3. A black window opens. It checks for Python and installs OpenCode +
   the needed packages automatically.
   - If it asks anything, just press **Enter** or click through.
   * If OpenCode installation completely fails, read the note at the bottom
     of this page titled **“OpenCode did not install.”*
4. When you see **DONE**, the tool is fully installed.

## Step 4 — Tell the AI which provider to use (once)  ✔

OpenCode needs to know which AI you have (OpenAI, Anthropic, Gemini, or a
free local model).

1. Open a **Command Prompt** (press `Windows` key, type `cmd`, press Enter).
2. Type:  `opencode`  and press Enter.
3. Follow the on-screen menu to sign in to your AI provider (you need an API
   key from that provider). Then type `exit` to close it.
   - Want an easy free option? Search “opencode + free model provider”
     (e.g. using a local model via Ollama) — many guides exist.

## Step 5 — Start the tool  ✔

1. In the tool folder, **double-click `start_hidden.vbs`**.
2. **Nothing visible happens** — that is correct! It is now watching silently.
3. To check it is alive: press **Ctrl + Alt + A**.

## Step 6 — Use it  ✔

1. **Copy** any text (code, a question, a bug, anything — inside any app).
2. Press **Ctrl + Alt + A**.
3. You will see a small **”wait .”** text with moving dots on the taskbar —
   that means the AI is answering.
4. It disappears and the **answer is now in your clipboard**. Paste anywhere
   with **Ctrl + V**.

---

## How to stop the tool

- Double-click **`stop.bat`** in the tool folder. Done.

## How to change appearance, show/hide things, or the AI mode

No code editing needed. Double-click **`start_settings.vbs`** (in the tool
folder) and a settings window opens where you can:

- Choose the **AI mode**: `Solve` (answer directly), `Explain` (explain it,
  not just the answer) or `Translate` (to the language you type).
- **Show or hide** the manual search bar and the wait note.
- Pick the **color**, **opacity**, **text size** and **position** (bottom
  taskbar / top) of the bar and the wait note.
- **Reset** fills everything with the stealth default (only `Solve` on, search
  bar off, wait note barely visible); **Submit** saves and (if you leave the
  checkbox on) restarts the tool with the new settings automatically.

To change the **hotkeys**, do it from the settings window — no code editing.

To change **low-level constants** (colors, ports, timeouts), open `src/main.py`
in a text editor and edit lines near the top (see README).

---

## Problems?

| Problem | Fix |
|---|---|
| “Python is NOT installed” appears in setup | Install Python (Step 1) and redo Step 3 |
| Ctrl+Alt+A does nothing after start | The tool needs `pynput` + `pyperclip`; run setup.bat again |
| “wait” appears then error flashes | Run `opencode` once and complete the provider sign-in (Step 4) |
| Setup opencode step failed | See section below |

### OpenCode did not install
- Windows: install **Node.js** from https://nodejs.org first, then in a
  command prompt run:  `npm i -g opencode-ai@latest`
- Or try:  `winget install SST.opencode`
- Then run `opencode` once to finish provider setup, and run `setup.bat` again.

---
*For more detail, read `REPORT.md`.*