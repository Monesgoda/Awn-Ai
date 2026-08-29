"""
StealthClip  (main.py)  --  Windows, 100% local

Runs silently in the background (no tray, no window). Copy any text, press
Ctrl+Alt+A and the clipboard content goes DIRECTLY to the local opencode agent
running on YOUR machine at 127.0.0.1 -- ports 30231 and 8051, nothing else, no
internet. No bar, no Enter key: the only feedback is a small "wait ." text with
animated dots sitting directly on the Windows taskbar. When the answer is ready
it is copied back into your clipboard and the note disappears. If the clipboard
is empty, a tiny near-invisible bar appears so you can type manually.

The bar is stealth by default: a calm dark color, no border, no chrome, low
window opacity. Its color, transparency and text size are customizable from
the settings window.

The script only ever reaches 127.0.0.1 (loopback). If the local opencode
server isn't running yet it starts one (visible nowhere, CREATE_NO_WINDOW).

Everything is configurable from the Settings window (settings_gui.py): a set
of hotkeys, each bound to its own action (solve / explain / translate /
custom prompt), show/hide the search bar and the wait note, their colors,
transparency and position. Settings live in settings.json.

Run it:    python main.py        (or double-click start_hidden.vbs)
Settings:  python settings_gui.py         (or double-click start_settings.vbs)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.request
import urllib.error

import pyperclip
from pynput import keyboard

import settings as cfg

# ---------------------------------------------------------------- config

VERSION = "1.4.0"                  # tool version (sent in the request header)
BAR_W, BAR_H = 500, 45             # search bar size
BAR_BOTTOM_PX = 50                 # distance from bottom of screen (above taskbar)
WINDOW_ALPHA = 0.45                # very faded, blends into the desktop
MAX_WAIT_SECONDS = 300             # timeout for one request
MAX_CLIP_CHARS = 8000              # clip the request if it's enormous
ERROR_MS = 2600                    # how long an error message stays visible

LOCAL_PORTS = [30231, 8051]        # THE ONLY PORTS USED -- loopback, no internet
SERVE_START_TRIES = 60             # wait up to ~30s for the server to come up

# tiny bottom progress note shown ONLY while the job is running,
# sits directly on the Windows taskbar (same shape, soft visibility)
NOTE_W, NOTE_H = 200, 32           # status bar size
NOTE_ALPHA = 0.60                  # visible but light, taskbar shows through
DOT_INTERVAL_MS = 300              # dot animation speed

THEME_BG = "#0d0d0d"               # fallback transparent-color key (bar bg is themed)
FIELD_BG = "#1a1a2e"               # fallback entry background
TEXT_FG = "#c8c8d8"                # entry text color (readable over any bar color)
PLACEHOLDER_FG = "#5a5a6a"         # placeholder text
ACCENT = "#7c5cff"                 # caret / status accent

_PX_BG = "#010203"                 # fixed invisible color used only as the
                                   # per-pixel transparent key for the bar, so
                                   # the user-picked bar_color stays visible.

PLACEHOLDER_TEXT = "Paste (Ctrl+V) or type a request…"

# live settings from settings.json (see settings.py / settings_gui.py)
SETTINGS = cfg.load_settings()

# ---------------------------------------------------------------- AI modes

PROMPT_SOLVE = (
    "You are a silent coding assistant. The user sends you a coding question. "
    "Reply with ONLY the solution, ready to be pasted: solve the request "
    "directly and give the final answer or clean working code -- no "
    "explanation, no headings, no backticks or ``` fences, no markdown. "
    "If the request isn't code, reply with just the result."
)

PROMPT_EXPLAIN = (
    "You are a patient tutor. The user sends you a request. Explain how it "
    "works and teach the user: give reasoning, steps and insight, but do NOT "
    "just hand over the final answer. If it is code, show it AND explain it. "
    "Answer in a clear, helpful way."
)

PROMPT_TRANSLATE = (
    "You are a professional translator. Translate the user's text into "
    "{target}. Reply with ONLY the translation -- no explanation, no quotes, "
    "no headings, no markdown."
)

def _build_prompt(action: dict) -> str:
    """Return the system prompt for one hotkey action (mode)."""
    mode = (action or {}).get("mode", "solve")
    if mode == "explain":
        return PROMPT_EXPLAIN
    if mode == "translate":
        target = str(action.get("target")
                     or SETTINGS.get("translate_target", "English")).strip() \
            or "English"
        return PROMPT_TRANSLATE.format(target=target)
    if mode == "custom":
        return (action.get("prompt") or "").strip() or PROMPT_SOLVE
    return PROMPT_SOLVE

# ---------------------------------------------------------------- output cleaning

_ANSI_RE = re.compile(r"\x1B\[[0-9;?]*[A-Za-z]")
_FENCE_RE = re.compile(r"^\s*```[a-zA-Z]*\s*$")


def _strip_fences(text: str) -> str:
    """Remove ```code``` fences and a wrapping pair of single backticks,
    so only clean code reaches the clipboard."""
    out = (text or "").strip()
    lines = out.splitlines()
    if lines and _FENCE_RE.match(lines[0]):
        lines = lines[1:]
    if lines and _FENCE_RE.match(lines[-1].strip()):
        lines = lines[:-1]
    out = "\n".join(lines).strip()
    if out.startswith("`") and out.endswith("`") and len(out) > 1:
        out = out[1:-1].strip()
    return out


def _clean_opencode_output(stdout: str) -> str:
    """opencode run prints a header line like '> build · big-pickle' plus ANSI
    colors; the answer is the last part of stdout. Strip all of that."""
    kept = []
    for line in _ANSI_RE.sub("", stdout or "").splitlines():
        s = line.strip()
        if not s or s.startswith(">"):      # skip header/summary lines
            continue
        kept.append(s)
    return _strip_fences("\n".join(kept))


# ---------------------------------------------------------------- local backend
#
# The tool talks ONLY to 127.0.0.1:<one of LOCAL_PORTS>. opencode serve binds
# to 127.0.0.1 by default, so nothing ever leaves the machine.

def _probe_server(port: int, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=timeout):
            return True
    except Exception:
        return False


def _start_local_server(port: int):
    """Spawn `opencode serve` on 127.0.0.1:<port>, hidden (CREATE_NO_WINDOW).
    Fully local loopback - the process binds to the machine only."""
    exe = shutil.which("opencode")
    if not exe:
        raise RuntimeError("opencode not found in PATH")
    if exe.lower().endswith((".cmd", ".bat")):
        cmd = [os.environ.get("COMSPEC", "cmd.exe"), "/c", exe]
    else:
        cmd = [exe]
    subprocess.Popen(
        cmd + ["serve", "--hostname", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=0x08000000,          # CREATE_NO_WINDOW: no terminal flash
    )
    for _ in range(SERVE_START_TRIES):
        if _probe_server(port):
            return
        time.sleep(0.5)
    raise RuntimeError(f"local server on port {port} did not start")


def _ensure_local_server() -> str:
    """Return the base URL of a reachable local opencode server on one of
    LOCAL_PORTS, starting one if necessary. Never touches another port."""
    for port in LOCAL_PORTS:
        if _probe_server(port):
            return f"http://127.0.0.1:{port}"
    _start_local_server(LOCAL_PORTS[0])
    return f"http://127.0.0.1:{LOCAL_PORTS[0]}"


def _post_json(base: str, path: str, payload: dict):
    req = urllib.request.Request(
        base + path, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": f"StealthClip/{VERSION}"})
    with urllib.request.urlopen(req, timeout=MAX_WAIT_SECONDS + 30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _ask_local_http(prompt: str) -> str:
    """Send the prompt to the LOCAL opencode server (loopback only) and read
    the answer out of its JSON reply."""
    base = _ensure_local_server()
    session = _post_json(base, "/session", {})
    sid = session.get("id")
    if not sid:
        raise RuntimeError("could not create a local session")

    body = {
        "sessionID": sid,
        "noTool": True,
        "parts": [{"type": "text", "text": prompt}],
    }
    reply = _post_json(base, f"/session/{sid}/message", body)

    text = ""
    for part in reply.get("parts", []):
        if part.get("type") == "text":
            text += part.get("text", "") or ""
    if not text.strip():
        raise RuntimeError("local agent returned an empty reply")
    return _strip_fences(text.strip())


def _opencode_command():
    """Resolve the opencode executable for the one-shot fallback."""
    exe = shutil.which("opencode")
    if not exe:
        return None
    if exe.lower().endswith((".cmd", ".bat")):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", exe]
    return [exe]


def _ask_opencode_run(prompt: str) -> str:
    """Fallback: one-shot `opencode run` (still local CLI, no API calls)."""
    cmd = _opencode_command()
    if not cmd:
        raise RuntimeError("opencode not found in PATH")
    flags = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
    try:
        proc = subprocess.run(
            cmd + ["run", "--format", "default", prompt],
            capture_output=True, timeout=MAX_WAIT_SECONDS,
            encoding="utf-8", errors="replace", **flags)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timed out after {MAX_WAIT_SECONDS}s")
    if proc.returncode != 0:
        raise RuntimeError(f"opencode exited {proc.returncode}")
    answer = _clean_opencode_output(proc.stdout)
    if not answer:
        raise RuntimeError("opencode returned an empty reply")
    return answer


def ask_opencode(prompt: str) -> str:
    """Ask the local agent. Prefers the always-on local server on 127.0.0.1
    (ports 30231 / 8051), falls back to one-shot `opencode run`."""
    try:
        return _ask_local_http(prompt)
    except Exception:
        return _ask_opencode_run(prompt)


# ---------------------------------------------------------------- tiny UI

class StealthClipAgent:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.bar = None
        self.entry = None
        self.status = None
        self.note = None
        self._dot_job = None
        self._dot_count = 0
        self._busy = False
        self._close_job = None

        self.actions = cfg.normalize_bindings(SETTINGS.get("hotkeys"))
        bindings = {}
        for act in self.actions:
            if not act.get("enabled", True):
                continue
            hk = act.get("hotkey")
            if not hk or hk in bindings:
                continue
            bindings[hk] = (lambda a=act: self.root.after(0, lambda a=a: self._on_hotkey(a)))
        self.listener = keyboard.GlobalHotKeys(bindings) if bindings else None
        if self.listener:
            self.listener.start()

        self.root.mainloop()

    # ---------------------------------------------------- activation / bar

    def _on_hotkey(self, action):
        try:
            clip = pyperclip.paste()
        except Exception:
            clip = ""
        if clip and clip.strip():
            # clipboard has text -> send straight to the AI, no bar, no Enter
            self._submit_text(clip.strip()[:MAX_CLIP_CHARS], action)
        elif SETTINGS.get("show_bar", True):
            # empty clipboard -> show the bar so you can type manually
            self._show_bar(clip, action)

    def _show_bar(self, initial_text: str = "", action: dict = None):
        self._destroy_bar()
        self._bar_action = action

        bar_color = SETTINGS.get("bar_color", FIELD_BG)
        alpha = SETTINGS.get("bar_alpha", WINDOW_ALPHA)
        bar_font = max(8, int(SETTINGS.get("bar_font_size", 11)))

        self.bar = tk.Toplevel(self.root)
        self.bar.overrideredirect(True)      # no title bar / window chrome
        self.bar.attributes("-topmost", True)
        self.bar.attributes("-alpha", alpha)
        self.bar.attributes("-transparentcolor", _PX_BG)   # shows bar_color below
        self.bar.configure(bg=bar_color)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.bar.geometry(f"{BAR_W}x{BAR_H}+{(sw - BAR_W)//2}+{sh - BAR_H - BAR_BOTTOM_PX}")

        frame = tk.Frame(self.bar, bg=bar_color)
        frame.pack(fill="both", expand=True)

        self.entry = tk.Entry(
            frame, font=("Consolas", bar_font), bg=bar_color, fg=TEXT_FG,
            insertbackground=ACCENT, relief="flat", bd=0,
            highlightthickness=0, highlightbackground=bar_color,
            highlightcolor=bar_color,
        )
        self.entry.pack(side="left", fill="both", expand=True, ipady=6, padx=(8, 2), pady=3)

        self.status = tk.Label(
            frame, text="\u2220", font=("Segoe UI", 9), bg=bar_color, fg=ACCENT, padx=6
        )
        self.status.pack(side="right", padx=(0, 8))

        self.entry.bind("<Return>", lambda e: self._on_submit())
        self.entry.bind("<Escape>", lambda e: self._destroy_bar())
        self.bar.bind("<FocusOut>", lambda e: self._schedule_close_if_unfocused())

        if initial_text and initial_text.strip():
            self.entry.insert(0, initial_text[:MAX_CLIP_CHARS])
            self.entry.select_range(0, "end")
        else:
            self.entry.insert(0, PLACEHOLDER_TEXT)
            self.entry.config(fg=PLACEHOLDER_FG)

        self.bar.update_idletasks()
        self.bar.deiconify()
        self.bar.lift()
        self.bar.focus_force()
        self.entry.focus_set()

    def _schedule_close_if_unfocused(self):
        if self.bar is None:
            return
        if self._close_job:
            self.root.after_cancel(self._close_job)
        self._close_job = self.root.after(300, self._close_if_unfocused)

    def _close_if_unfocused(self):
        self._close_job = None
        if self.bar is None:
            return
        try:
            if not self.bar.focus_displayof():
                self._destroy_bar()
        except Exception:
            self._destroy_bar()

    def _destroy_bar(self):
        if self._close_job:
            try:
                self.root.after_cancel(self._close_job)
            except Exception:
                pass
            self._close_job = None
        if self.bar is not None:
            try:
                self.bar.destroy()
            except Exception:
                pass
        self.bar = None

    # ---------------------------------------------------- bottom wait-note

    def _start_note(self):
        """Small transparent note (top or bottom, per settings), shown ONLY
        while the job runs, with animated dots so you know it's still working."""
        self._stop_note()
        if not SETTINGS.get("show_wait", True):
            return
        note_color = SETTINGS.get("wait_color", "#b0b0c0")
        alpha = SETTINGS.get("wait_alpha", NOTE_ALPHA)
        note_font = max(8, int(SETTINGS.get("wait_font_size", 10)))
        below = SETTINGS.get("wait_position", "bottom") != "top"

        self.note = tk.Toplevel(self.root)
        self.note.overrideredirect(True)
        self.note.attributes("-topmost", True)
        self.note.attributes("-alpha", alpha)
        self.note.attributes("-transparentcolor", THEME_BG)    # text only, no box
        self.note.configure(bg=THEME_BG)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        y = sh - NOTE_H if below else 4
        self.note.geometry(f"{NOTE_W}x{NOTE_H}+{(sw - NOTE_W)//2}+{y}")
        self.note_label = tk.Label(
            self.note, text="wait .", font=("Segoe UI", note_font),
            bg=THEME_BG, fg=note_color
        )
        self.note_label.pack(fill="both", expand=True)
        self.note.update_idletasks()
        self.note.deiconify()
        self.note.lift()
        self._dot_count = 0
        self._animate_dots()

    def _animate_dots(self):
        if self.note is None:
            return
        self._dot_count = (self._dot_count % 4) + 1
        self.note_label.config(text="wait " + "." * self._dot_count)
        self._dot_job = self.root.after(DOT_INTERVAL_MS, self._animate_dots)

    def _stop_note(self):
        if self._dot_job:
            try:
                self.root.after_cancel(self._dot_job)
            except Exception:
                pass
            self._dot_job = None
        if self.note is not None:
            try:
                self.note.destroy()
            except Exception:
                pass
        self.note = None

    # ---------------------------------------------------- flash status

    def _flash(self, text: str, color: str, keep_ms: int):
        """Briefly show a background-free status line (text only), then close.
        Position follows the wait-note setting (top/bottom)."""
        if self.bar is not None:
            try:
                self.bar.destroy()
            except Exception:
                pass
        self.bar = tk.Toplevel(self.root)
        self.bar.overrideredirect(True)
        self.bar.attributes("-topmost", True)
        self.bar.attributes("-alpha", WINDOW_ALPHA)
        self.bar.attributes("-transparentcolor", THEME_BG)    # text only, no box
        self.bar.configure(bg=THEME_BG)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        below = SETTINGS.get("wait_position", "bottom") != "top"
        y = sh - BAR_H - BAR_BOTTOM_PX if below else 4
        self.bar.geometry(f"{BAR_W}x{BAR_H}+{(sw - max(220, len(text) * 8))//2}+{y}")
        lbl = tk.Label(
            self.bar, text=text, bg=THEME_BG, fg=color,
            font=("Segoe UI", 12, "bold"), padx=10,
        )
        lbl.pack(fill="both", expand=True)
        self.bar.update_idletasks()
        self.bar.deiconify()
        self.bar.lift()
        self._close_job = self.root.after(keep_ms, self._destroy_bar)

    # ---------------------------------------------------- flow

    def _on_submit(self):
        if self._busy or self.entry is None:
            return
        text = self.entry.get().strip()
        if not text or text == PLACEHOLDER_TEXT:
            self._destroy_bar()
            return
        action = getattr(self, "_bar_action", None)
        self._destroy_bar()
        self._submit_text(text, action)

    def _submit_text(self, text: str, action: dict = None):
        """Fire the request immediately: no bar, just the taskbar "wait" note."""
        if self._busy:
            return
        self._busy = True

        # bottom "wait .." note appears now (the only visible feedback)
        self._start_note()

        threading.Thread(target=self._process, args=(text, action), daemon=True).start()

    def _process(self, prompt: str, action: dict = None):
        final_prompt = f"{_build_prompt(action)}\n\nRequest:\n{prompt}"
        try:
            result = ask_opencode(final_prompt)
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._finish_error(err))
            return
        self.root.after(0, lambda code=result: self._finish_ok(code))

    def _finish_ok(self, code: str):
        self._stop_note()                     # hide the wait-dots, no success message
        try:
            pyperclip.copy(code)
        except Exception:
            pass
        self._busy = False

    def _finish_error(self, msg: str):
        self._stop_note()
        self._busy = False
        short = (msg or "Error").strip()[:60]
        self._flash(short, "#ff5252", ERROR_MS)


if __name__ == "__main__":
    try:
        StealthClipAgent()
    except KeyboardInterrupt:
        sys.exit(0)