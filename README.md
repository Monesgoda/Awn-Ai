# 🕵️ StealthClip — invisible clipboard AI assistant
<img width="1408" height="768" alt="Gemini_Generated_Image_naziafnaziafnazi" src="https://github.com/user-attachments/assets/4223b3cf-0449-43d4-b684-8d6d618b7ed0" />

**Copy anything → press `Ctrl+Alt+A` → paste a ready answer.**

A tiny Windows background tool that sends what you copy to **your local
[OpenCode](https://opencode.ai) agent** (loopback only — 100% your machine)
and hands back a clean, ready-to-paste result. No console, no window, no tray
icon, no distractions. The only feedback while it works is a small animated
**“wait .”** note in the corner of the taskbar.

> **Stealth by design** — it’s meant to blend into your workflow: you keep
> living in your browser, editor or chat, hit one hotkey, and the answer is
> already in your clipboard.




## 🎯 What can you use it for?

Anything you’d normally open a separate AI tab for — without the tab:

- 🧮 **Quick problems & homework** — understand how to solve a math problem,
  a physics question, or a short assignment. Ask *Explain* to teach you the
  steps instead of just handing over the answer.
- 💻 **Code & debugging** — paste a snippet or an error, get clean working code
  or a fix ready to paste back.
- 🧠 **Quick reminders** — forgot a command, a shortcut, a formula, or a
  concept? Copied text or your prompt brings it back in seconds.
- 🛡️ **Programming & cybersecurity** — get explanations, snippets, CLI
  commands and concepts on the spot while you read or learn.
- 📚 **General studying** — translate a passage, summarize a paragraph, ask
  about anything you’re learning.

> Use it to **learn and build** — solve with understanding, not to cheat.
> The *Explain* mode exists exactly for that.

---

## ✨ Features

- ⚡ **Zero friction** — copy text, hit your hotkey, done. No Enter, no window.
- 🔇 **Truly silent** — `pythonw` launcher: no console, no tray, no popups.
- 🕵️ **Stealth UI** — per-pixel transparent windows, low opacity, subtle colors.
- ⌨️ **Multiple hotkeys** — each hotkey does its own thing:
  - `Ctrl+Alt+A` → **Solve** (direct answer)
  - `Ctrl+Alt+E` → **Explain** (teaches, no straight answer)
  - `Ctrl+Alt+T` → **Translate** (to a language you choose)
  - `Ctrl+Alt+B` → **Quick Ask** (your own custom prompt)
- 🧩 **Fully configurable** — colors, opacity, position, text size, AI modes —
  all from a small settings window.
- 🧵 **Non-blocking** — requests run in a background thread; nothing freezes.
- 🛡️ **100% local** — talks only to `127.0.0.1` (ports `30231` / `8051`).
- 🆓 **Open source** — MIT, no analytics, no accounts (except your own AI
  provider).

---

## 📹 Videos

> Placeholder — demo videos 

<video src="https://github.com/user-attachments/assets/57ddc8bd-54d1-4f54-add4-c014d4be8eaa" controls="controls" style="max-width: 100%;"></video>


---

## 🚀 Quick start (beginners: read [`INSTALL.md`](INSTALL.md))

1. **Install Python** — tick *“Add python.exe to PATH”* at https://python.org/downloads
2. **Install OpenCode**: `npm i -g opencode-ai@latest` *(needs Node.js)* or
   `winget install SST.opencode`
3. `pip install -r requirements.txt`
4. Run `opencode` once, sign in to your AI provider, type `exit`.
5. Double-click **`start_hidden.vbs`** → nothing appears (that’s correct).
6. Copy text → press **`Ctrl+Alt+A`** → wait for the dots → paste the answer.

> On Windows, double-click **`setup.bat`** and it checks/installs steps 1–4
> for you automatically.

---

## 🎮 Usage

| Action | Result |
|---|---|
| Copy text, press `Ctrl+Alt+A` | Clipboard text → AI immediately |
| `Ctrl+Alt+A` with empty clipboard | Tiny text bar appears → type → Enter |
| `start_settings.vbs` | Open the graphical settings window |
| `stop.bat` | Stop the background tool |

---

## ⚙️ Settings (graphical)

Double-click **`start_settings.vbs`** to open a compact settings window. It
scrolls internally, so it stays small on any screen. You can:

- **Hotkeys & Actions** — see, add, remove or change hotkeys; every hotkey
  has its own **mode**:
  - `Solve` — answer directly, no explanation
  - `Explain` — teach and break it down, no straight answer
  - `Translate` — change language (type the target, e.g. *English*)
  - `Custom` — your own prompt
  - Toggle each action **ON/OFF** without deleting it.
- **Search bar** — show/hide it, and pick its **color**, **opacity**, and
  **text size**.
- **Wait note** — show/hide it, and pick its **color**, **opacity**,
  **position** (bottom taskbar / top), and **text size**.

### Buttons

- **Reset** ↺ — applies the *stealth default*: only **Solve** stays on, the
  search bar is off, and the wait note is on but barely visible (faint pale
  white in the taskbar corner).
- **Submit** — saves your changes and closes the window. A checkbox above it
  controls what happens next:
  - ✅ **“Start the tool now after saving”** (default) — restarts the tool
    in the background with the new settings immediately.
  - ❌ Uncheck it — the tool is stopped and stays off until you launch it
    yourself with `start_hidden.vbs`.
- **Cancel** — close without saving.

Settings are stored in **`src/settings.json`** next to the code.

---

## 🖥️ Run commands

From the tool folder:

```text
# launch the background tool (silent, recommended)
start_hidden.vbs

# launch the tool from a console (for debugging)
python src/main.py

# open the settings window
start_settings.vbs

# stop the tool
stop.bat

# one-time install (Python + opencode + packages)
setup.bat
```

---

## 📁 Folder structure

```
stealth-clip-assistant/
├── src/                     # the source code (run here)
│   ├── main.py              # the background agent (the tool itself)
│   ├── settings.py          # settings store (settings.json) + defaults
│   ├── settings_gui.py      # graphical settings window
│   └── settings.json        # your personal settings (not committed)
├── start_hidden.vbs         # silent launcher (pythonw, no console)
├── start_settings.vbs       # opens the settings window
├── setup.bat                # one-click installer
├── stop.bat                 # stops the background tool
├── requirements.txt         # pip dependencies
├── README.md                # this page
├── INSTALL.md               # beginner, click-by-click guide
├── REPORT.md                # technical & security report
├── CHANGELOG.md             # version history
├── LICENSE                  # MIT
└── .gitignore
```

---

## ⚙️ Configuration (manual)

All low-level constants are at the top of **`src/main.py`**:

```python
WINDOW_ALPHA = 0.45             # lower = more invisible
LOCAL_PORTS = [30231, 8051]     # the ONLY ports ever used (loopback)
MAX_WAIT_SECONDS = 300          # request timeout
```

The **hotkeys and their actions** live in **`src/settings.json`** under `hotkeys`
— edit them from the settings window:

```json
"hotkeys": [
  { "hotkey": "<ctrl>+<alt>+a", "label": "Solve", "mode": "solve" },
  { "hotkey": "<ctrl>+<alt>+e", "label": "Explain", "mode": "explain" },
  { "hotkey": "<ctrl>+<alt>+t", "label": "Translate", "mode": "translate", "target": "English" },
  { "hotkey": "<ctrl>+<alt>+b", "label": "Quick Ask", "mode": "custom", "prompt": "…" }
]
```

- `mode: "solve"` → answer directly · `"explain"` → teach · `"translate"`
  (+ `target`) → translate · `"custom"` (+ `prompt`) → your own instruction.
  `enabled: true/false` turns an action off without deleting it.
- Type hotkeys in friendly form like `ctrl+alt+x` (modifiers: `ctrl`, `alt`,
  `shift`, `win`; keys: letters, numbers, or named keys like `space`, `f1`).

---

## 🔒 Privacy & security

- All requests go to **`127.0.0.1`** — the machine never talks to the
  internet through this tool.
- No telemetry, stores nothing, ignores everything except your hotkey and
  clipboard.
- ⚠️ The **AI model** is whatever you configure in OpenCode. Cloud models send
  your text to that provider. Want absolute privacy? Point OpenCode at a
  local model (e.g. Ollama) and you’re fully offline.

---

## 📚 Documentation

| File | Contents |
|---|---|
| [`INSTALL.md`](INSTALL.md) | Beginner, click-by-click setup |
| [`REPORT.md`](REPORT.md) | Full technical & security report |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

---

## 🧰 Requirements

- Windows 10 / 11
- Python 3.10+
- OpenCode CLI (`opencode`) on PATH
- Python packages: `pyperclip`, `pynput`

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).
