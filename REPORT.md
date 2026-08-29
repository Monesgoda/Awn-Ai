# REPORT — StealthClip (src/main.py)

**Version:** 1.4.0 · **Platform:** Windows (tkinter / `pynput`) · **License:** MIT

---

## 1. Overview

A background utility that turns your clipboard + a hotkey into a silent,
local AI coding assistant. Copy anything, press `Ctrl+Alt+A`, and the text is
sent to a **local** AI agent; the answer is copied back into your clipboard.
The entire interaction is designed to leave almost no visual trace:

- No tray icon, no window, no console on start (launcher uses `pythonw.exe`).
- The **only** feedback while working is a small animated **“wait .”** note
  drawn over the Windows taskbar.
- The manual input bar (only shown when the clipboard is empty) is near
  invisible: `#0d0d0d` theme on a per-pixel transparent window at 45% alpha.

## 2. Feature matrix

| Feature | Detail |
|---|---|
| Activation | Global hotkey(s) — several, each bound to its own action |
| Primary path | Clipboard has text → sent to the AI **immediately** (no Enter) |
| Fallback path | Empty clipboard → near-invisible bar appears for manual typing |
| AI modes | `solve` / `explain` / `translate` / `custom` (selectable in settings) |
| Feedback | “wait .” animated dots on the taskbar, only while processing |
| Settings UI | Graphical editor for modes, colors, opacity and positions |
| Result | Clean answer copied to clipboard (markdown fences / ANSI stripped) |
| Backend | Local **opencode** server on `127.0.0.1` (auto-started, hidden) |
| Fallback backend | One-shot `opencode run` CLI if the HTTP server is unreachable |
| Network | **Loopback only** — ports `30231` / `8051`, never the internet |
| Ops | `start_hidden.vbs` (run), `start_settings.vbs` (settings), `stop.bat` (kill), `setup.bat` (install) |

## 3. Architecture / data flow

```
                        +---------------------------------------------+
 Clipboard --> hotkey --> pyperclip.paste()                          |
                        |    | has text --> _submit_text()           |
                        |    +--> empty --------> _show_bar() (manual)|
                        +--------+-----------------------------------+
                                v
                      _start_note()  "wait ." on taskbar
                                |  (background thread)
                                v
                   ask_opencode(final_prompt)
                     |  try HTTP local server       --> 127.0.0.1:30231/8051
                     |  {"session","message","noTool":true}
                     |  except any error            --> opencode run CLI
                                |
                                v
                _finish_ok     --> pyperclip.copy(answer)
                _finish_error  --> _flash(short error text)
```

Threading: the UI (Tk mainloop) and the request run on separate threads;
the request thread reports back via `root.after(0, ...)` which is safe to
call from other threads in CPython Tkinter.

## 4. Stealth design

- **Per-pixel transparency** — `-transparentcolor` leaves only the content
  visible; the bar uses a fixed invisible key (`#010203`) so the user-picked
  bar color is actually shown through the window.
- **Low opacity** — bar `bar_alpha` (default 0.45), note `wait_alpha`.
- **Calm palette** — defaults are dark (`#1A1A2E` bar, pale note text),
  all customizable from the settings window.
- **No chrome** — `overrideredirect(True)`, `highlightthickness=0`.
- **No success popup** — the original “Done!” flash was removed; the note
  simply disappears, implying success without any UI.
- **Reset (stealth) profile** — locks everything except `Solve`, turns the
  search bar off, and keeps a barely-visible note (faint pale white, low
  opacity) in the taskbar corner: you see it, someone nearby won’t.
- **Position** — the bar sits above the taskbar; the note sits *on* the
  taskbar (or top of screen) so it looks like part of the Windows UI.

## 5. Security

- **Loopback only** — all HTTP goes to `127.0.0.1`; `opencode serve` is
  spawned with `--hostname 127.0.0.1`. No traffic leaves the machine when a
  local/offline model is used.
- **No server exposed** — if the ports are unreachable the tool falls back to
  the CLI, which also runs locally.
- **Hidden process spawn** — `creationflags=0x08000000` (`CREATE_NO_WINDOW`).
- **Please note** — the *model* itself may be cloud-based (your provider’s API
  key inside OpenCode). If you require total privacy, configure OpenCode with
  a fully local model (e.g. Ollama). The tool alone never dials out.
- It does **not** collect or upload any data, telemetry, or keys.
- No third-party analytics, no locking, no persistence.

## 6. Configuration reference

### 6.1 Graphical (`start_settings.vbs` → `src/settings.json`)

| Setting | Default | Meaning |
|---|---|---|
| `hotkeys` | see below | list of hotkey → action bindings |
| `translate_target` | `English` | Language for translate mode |
| `show_bar` | `true` | Search bar visible (false = hotkey-only) |
| `bar_color` | `#1A1A2E` | Bar background color (visible) |
| `bar_alpha` | `0.45` | Bar opacity |
| `bar_font_size` | `11` | Bar text size |
| `show_wait` | `true` | Wait note visible |
| `wait_position` | `bottom` | `bottom` (taskbar) or `top` |
| `wait_color` | `#B0B0C0` | Wait note text color |
| `wait_alpha` | `0.60` | Wait note opacity |
| `wait_font_size` | `10` | Wait note text size |

Each hotkey is an action: `solve` / `explain` / `translate` (+ `target`) /
`custom` (+ `prompt`), with an `enabled` flag.

**Buttons:**
- **Reset** — applies the stealth default (only `Solve` on, bar off, faint note).
- **Submit** — saves and closes the window. The **“Start the tool now after
  saving”** checkbox decides whether it (re)starts the tool in the background
  immediately (`restart_tool()` in `settings_gui.py`) or only saves & stops.

### 6.2 Code constants (`src/main.py` top)

| Constant | Default | Meaning |
|---|---|---|
| `BAR_W, BAR_H` | `500, 45` | Manual bar size |
| `BAR_BOTTOM_PX` | `50` | Bar distance above taskbar |
| `WINDOW_ALPHA` | `0.45` | Bar window opacity |
| `NOTE_W, NOTE_H` | `200, 32` | Taskbar note size |
| `NOTE_ALPHA` | `0.60` | Note opacity |
| `DOT_INTERVAL_MS` | `300` | Dots animation speed |
| `MAX_WAIT_SECONDS` | `300` | AI request timeout |
| `MAX_CLIP_CHARS` | `8000` | Clipboard truncation limit |
| `ERROR_MS` | `2600` | Error text display time |
| `LOCAL_PORTS` | `[30231, 8051]` | Only ports ever contacted |
| `SERVE_START_TRIES` | `60` | Startup wait (~30 s) for server |
| `THEME_BG` | `#0d0d0d` | Fallback transparent-color key |

Hotkeys are **not** constants anymore — they live in `src/settings.json`.

### 6.3 AI modes

| Mode | Prompt intent |
|---|---|
| `solve` (default) | Direct answer / clean code, copy-ready, no explanation |
| `explain` | Tutor: teaches, shows and explains, avoids a straight answer |
| `translate` | Translates input to `translate_target`, only the translation |
| `custom` | Uses a prompt you write yourself |

The selected prompt is injected as the system message before the request:
`f"{_build_prompt(action)}\n\nRequest:\n{prompt}"`.

## 7. Dependencies

- Python 3.10+ (uses `tkinter`, bundled with Python on Windows).
- `pyperclip` — clipboard read/write.
- `pynput` — global keyboard listener.
- **OpenCode CLI** (`opencode`) — the AI engine; on PATH.
  Install: `npm i -g opencode-ai@latest` or `winget install SST.opencode`
  or `choco install opencode` / `scoop install opencode`.

## 8. Files in this project

```
stealth-clip-assistant/
├── src/                     # the source code (run here)
│   ├── main.py              # the background agent (the tool itself)
│   ├── settings.py          # settings store (settings.json) + defaults
│   ├── settings_gui.py      # graphical settings window
│   └── settings.json        # your personal settings (not committed)
├── start_hidden.vbs         # silent launcher (pythonw, no console)
├── start_settings.vbs       # opens the settings window
├── setup.bat                # one-click installer (Python + opencode + packages)
├── stop.bat                 # stops the background tool
├── requirements.txt         # pip dependencies
├── README.md                # project page
├── INSTALL.md               # beginner guide
├── REPORT.md                # this document
├── CHANGELOG.md             # version history
├── LICENSE                  # MIT
└── .gitignore
```

## 9. Running

```
# start (silent, recommended)
start_hidden.vbs

# start (console, debugging)
python src/main.py

# stop
stop.bat
```

## 10. Troubleshooting quick map

| Symptom | Cause / fix |
|---|---|
| Nothing on hotkey | `pynput`/`pyperclip` missing → run `setup.bat` |
| Single beep, no answer | `opencode` not in PATH or not configured → run `opencode` once |
| Error text flashes red | Local server failed AND `opencode run` failed → check step 4 of INSTALL |
| Two bars on hotkey | An old instance is still running → run `stop.bat`, start again |

## 11. Versioning

See `CHANGELOG.md`. Version string lives in `VERSION` in the script and is
sent as the `User-Agent` on local HTTP requests (`StealthClip/<version>`).
