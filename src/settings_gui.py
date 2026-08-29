"""
StealthClip Settings GUI.

Edit every option -- your set of hotkeys (each bound to its own action:
solve / explain / translate / custom prompt), show/hide the search bar and
the wait note, colors, transparency, font size, position -- through a small
window that fits on screen and scrolls internally.

Two action buttons:
  * Reset    - fills the window with the stealth / default profile: only
               "Solve" is enabled, the search bar is off, and the wait note
               is on but so faint (pale white, low opacity) it is only
               barely visible in the taskbar corner.
  * Submit   - approves the current changes, saves them to settings.json,
               then closes this window. A checkbox decides what happens next:
               "Start the tool now after saving" (default ON) restarts the
               background tool instantly; if you uncheck it, the tool is
               stopped and stays off until you launch it yourself with
               start_hidden.vbs.

Run it:  python settings_gui.py    (or double-click start_settings.vbs)
"""

import os
import shutil
import subprocess
import sys
import time
import tkinter as tk
from tkinter import colorchooser, messagebox

import settings as cfg

BG = "#12121c"
PANEL = "#1a1a26"
FG = "#e0e0e0"
DIM = "#8a8a9a"
ACCENT = "#7c5cff"
FIELD = "#24243a"
GREEN = "#00e676"
RED = "#ff5252"

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(THIS_DIR, "main.py")

PALETTE = [
    "#0d0d0d", "#16213e", "#1a1a2e", "#223822",
    "#2b2b4a", "#3a2b1a", "#444455", "#5c3a78",
]

MODE_NAMES = [("Solve   - answer directly", "solve"),
              ("Explain - teach, no direct answer", "explain"),
              ("Translate - change language", "translate"),
              ("Custom - your own prompt", "custom")]


def _kill_tool():
    """Kill any running instance of the tool from this folder (no restart)."""
    ps = (
        "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like"
        " '*main.py*' } | ForEach-Object { Stop-Process -Id"
        " $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=15)
    except Exception:
        pass


def _run_proc(cmd):
    flags = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     **flags)


def restart_tool():
    """Kill any running instance of the tool, then start it again hidden so
    the fresh settings are active right away."""
    _kill_tool()
    time.sleep(0.5)
    exe = shutil.which("pyw.exe") or shutil.which("pythonw.exe")
    if exe:
        _run_proc([exe, MAIN_SCRIPT])


class SettingsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("StealthClip Settings")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        s = cfg.load_settings()
        self.bar_color = tk.StringVar(value=s.get("bar_color", "#1a1a2e"))
        self.bar_alpha = tk.DoubleVar(value=s.get("bar_alpha", 0.45))
        self.bar_font = tk.IntVar(value=s.get("bar_font_size", 11))
        self.show_bar = tk.BooleanVar(value=s.get("show_bar", True))
        self.show_wait = tk.BooleanVar(value=s.get("show_wait", True))
        self.wait_position = tk.StringVar(value=s.get("wait_position", "bottom"))
        self.wait_color = tk.StringVar(value=s.get("wait_color", "#b0b0c0"))
        self.wait_alpha = tk.DoubleVar(value=s.get("wait_alpha", 0.60))
        self.wait_font = tk.IntVar(value=s.get("wait_font_size", 10))

        self.run_after = tk.BooleanVar(value=True)

        self.rows = []
        self._build()
        self._load_rows(s.get("hotkeys"))
        self._bar_enable()
        self._wait_enable()
        self._bind_mousewheel()

        self.status = tk.Label(self.root, text="", bg=BG, fg=GREEN,
                               font=("Segoe UI", 9), wraplength=480, justify="left")
        self.status.pack(fill="x", padx=14, pady=(0, 4))

        self.center_window(540, 540)

    # ------------------------------------------------------------ UI

    def _build(self):
        # ---- header ----
        tk.Label(self.root, text="StealthClip Settings",
                 font=("Segoe UI", 12, "bold"), bg=BG, fg=FG).pack(
                 anchor="w", padx=14, pady=(10, 2))

        # ---- scrollable body ----
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        self.body_canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        self.body_scroll = tk.Scrollbar(body, orient="vertical",
                                        command=self.body_canvas.yview)
        self.body_canvas.configure(yscrollcommand=self.body_scroll.set)
        self.body_scroll.pack(side="right", fill="y")
        self.body_canvas.pack(side="left", fill="both", expand=True)

        self.body_inner = tk.Frame(self.body_canvas, bg=BG)
        self._body_window = self.body_canvas.create_window((0, 0),
                                                           window=self.body_inner,
                                                           anchor="nw")
        self.body_inner.bind(
            "<Configure>",
            lambda e: self.body_canvas.configure(
                scrollregion=self.body_canvas.bbox("all")))
        self.body_canvas.bind(
            "<Configure>",
            lambda e: self.body_canvas.itemconfigure(
                self._body_window, width=e.width))

        content = self.body_inner

        # ---------- Hotkeys / actions ----------
        tk.Label(content, text="Hotkeys & Actions  (each hotkey does its own thing)",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(
                 anchor="w", padx=14, pady=(4, 2))

        hk_wrap = tk.Frame(content, bg=PANEL)
        hk_wrap.pack(fill="x", padx=14)

        self.hk_canvas = tk.Canvas(hk_wrap, bg=PANEL, highlightthickness=0, height=210)
        self.hk_scroll = tk.Scrollbar(hk_wrap, orient="vertical",
                                      command=self.hk_canvas.yview)
        self.hk_canvas.configure(yscrollcommand=self.hk_scroll.set)
        self.hk_inner = tk.Frame(self.hk_canvas, bg=PANEL)
        self.hk_inner.bind("<Configure>",
                           lambda e: self.hk_canvas.configure(
                               scrollregion=self.hk_canvas.bbox("all")))
        self.hk_canvas.create_window((0, 0), window=self.hk_inner, anchor="nw")
        self.hk_scroll.pack(side="right", fill="y")
        self.hk_canvas.pack(fill="both", expand=True)

        add = tk.Button(content, text="+ Add action", command=self._add_row,
                        bg=FIELD, fg=FG, relief="flat", font=("Segoe UI", 9),
                        padx=12, pady=3, activebackground="#3a3a58")
        add.pack(anchor="w", padx=14, pady=(4, 0))

        tk.Label(content, text="Hotkey format: ctrl+alt+x,  ctrl+shift+f1,  "
                               "alt+space,  etc. (letters / numbers / named keys)",
                 bg=BG, fg=DIM, font=("Segoe UI", 8)).pack(
                 anchor="w", padx=14, pady=(0, 2))

        # ---------- Search bar ----------
        tk.Label(content, text="Search Bar  (appears with an empty clipboard)",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(
                 anchor="w", padx=14, pady=(6, 2))
        self.bar_rows = self._bar_panel(content)

        # ---------- Wait note ----------
        tk.Label(content, text="Wait Note  (progress indication)",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(
                 anchor="w", padx=14, pady=(6, 2))
        self.wait_rows = self._wait_panel(content)

        # ---------- Actions ----------
        opt = tk.Frame(self.root, bg=BG)
        opt.pack(fill="x")
        tk.Checkbutton(opt, text="Start the tool now after saving (uncheck to "
                                 "only save & stop)",
                       variable=self.run_after, bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, font=("Segoe UI", 9),
                       highlightthickness=0, bd=0).pack(side="left", padx=14)

        btns = tk.Frame(self.root, bg=BG)
        btns.pack(fill="x", pady=(6, 8))
        tk.Button(btns, text="Reset  \u21ba", command=self._reset,
                  bg="#3a3a58", fg=FG, font=("Segoe UI", 10), relief="flat",
                  padx=16, pady=5, activebackground="#4a4a6a").pack(
                  side="left", padx=(14, 6))
        tk.Button(btns, text="Submit", command=self._submit,
                  bg="#2fd05a", fg="#062a12", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=22, pady=5, activebackground="#37e469").pack(
                  side="right", padx=(6, 14))
        tk.Button(btns, text="Cancel", command=self.root.destroy, bg="#33334a",
                  fg=FG, font=("Segoe UI", 10), relief="flat", padx=16, pady=5,
                  activebackground="#44445f").pack(side="right", padx=6)

    def _bind_mousewheel(self):
        def _onwheel(event):
            self.body_canvas.yview_scroll(int(-event.delta / 120), "units")
        self.root.bind_all("<MouseWheel>", _onwheel)

    # ---- hotkey rows ----
    def _load_rows(self, hotkeys):
        for item in (hotkeys or []):
            self._add_row(item)

    def clear_rows(self):
        for row in list(self.rows):
            self._remove_row(row)
        self.rows = []

    def _add_row(self, data=None):
        data = data or {}
        row = {
            "label": tk.StringVar(value=data.get("label", "New Action")),
            "mode": tk.StringVar(value=data.get("mode", "solve")),
            "hk": tk.StringVar(value=str(data.get("hotkey", "")).replace("<", "").replace(">", "")),
            "target": tk.StringVar(value=data.get("target", "").strip() or "English"),
            "prompt": tk.StringVar(value=data.get("prompt", "")),
            "on": tk.BooleanVar(value=bool(data.get("enabled", True))),
        }

        fr = tk.Frame(self.hk_inner, bg=PANEL, bd=1, relief="groove")
        fr.pack(fill="x", padx=4, pady=3)

        head = tk.Frame(fr, bg=PANEL)
        head.pack(fill="x", padx=6, pady=(4, 0))

        tk.Label(head, text="Name:", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(head, textvariable=row["label"], bg=FIELD, fg=FG,
                 insertbackground=FG, relief="flat", width=12,
                 font=("Segoe UI", 9)).pack(side="left", padx=(2, 8))

        tk.Label(head, text="Mode:", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).pack(side="left")
        mode_var = row["mode"]
        om = tk.OptionMenu(head, mode_var, *[m for _, m in MODE_NAMES],
                           command=lambda _v, r=row: self._render_ctx(r))
        om.config(bg=FIELD, fg=FG, activebackground="#3a3a58", activeforeground=FG,
                  highlightthickness=0, relief="flat", font=("Segoe UI", 9))
        om["menu"].config(bg=FIELD, fg=FG)
        om.pack(side="left", padx=(2, 8))

        tk.Label(head, text="Hotkey:", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(head, textvariable=row["hk"], bg=FIELD, fg=FG,
                 insertbackground=FG, relief="flat", width=14,
                 font=("Consolas", 9)).pack(side="left", padx=(2, 8))

        tk.Button(head, text="\u2715", command=lambda r=row: self._remove_row(r),
                  bg="#3a2030", fg=RED, relief="flat", font=("Segoe UI", 10, "bold"),
                  bd=0, width=2, cursor="hand2").pack(side="right")

        row["on_btn"] = tk.Button(
            head, font=("Segoe UI", 8, "bold"), bd=0, width=4, cursor="hand2",
            command=lambda r=row: self._toggle_row(r))
        row["on_btn"].pack(side="right", padx=(0, 2))
        self._render_toggle(row)

        row["ctx"] = tk.Frame(fr, bg=PANEL)
        row["ctx"].pack(fill="x", padx=6, pady=(0, 4))
        self.rows.append(row)
        self._render_ctx(row)
        return row

    def _render_toggle(self, row):
        on = row["on"].get()
        row["on_btn"].config(
            text="ON" if on else "OFF",
            bg="#1f6b3a" if on else "#3a3a44",
            fg="#d6f5e0" if on else DIM,
            activebackground="#27924c" if on else "#4a4a55",
        )
        state = "normal" if on else "disabled"
        for w in row["on_btn"].master.winfo_children():
            if w is row["on_btn"]:
                continue
            self._set_state(w, state)

    def _toggle_row(self, row):
        row["on"].set(not row["on"].get())
        self._render_toggle(row)

    def _remove_row(self, row):
        row["ctx"].master.destroy()
        if row in self.rows:
            self.rows.remove(row)

    def _render_ctx(self, row):
        ctx = row["ctx"]
        for w in ctx.winfo_children():
            w.destroy()
        mode = row["mode"].get()
        if mode == "translate":
            tk.Label(ctx, text="Target language:", bg=PANEL, fg=DIM,
                     font=("Segoe UI", 9)).pack(side="left", padx=(10, 4))
            tk.Entry(ctx, textvariable=row["target"], bg=FIELD, fg=FG,
                     insertbackground=FG, relief="flat", width=18,
                     font=("Segoe UI", 9)).pack(side="left")
        elif mode == "custom":
            tk.Label(ctx, text="Prompt (how the AI should act):", bg=PANEL,
                     fg=DIM, font=("Segoe UI", 9)).pack(side="left", padx=(10, 4))
            tk.Entry(ctx, textvariable=row["prompt"], bg=FIELD, fg=FG,
                     insertbackground=FG, relief="flat", width=28,
                     font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)
        else:
            tip = ("Solves directly, no explanation" if mode == "solve"
                   else "Explains and teaches")
            tk.Label(ctx, text=tip, bg=PANEL, fg=DIM,
                     font=("Segoe UI", 9)).pack(side="left", padx=10)

    # ---- search bar panel ----
    def _bar_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", padx=14)
        tk.Checkbutton(frame, text="Show search bar", variable=self.show_bar,
                       command=self._bar_enable, bg=PANEL, fg=FG, selectcolor=PANEL,
                       activebackground=PANEL, font=("Segoe UI", 10),
                       highlightthickness=0, bd=0).grid(
                       row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 2))
        self._color_row(frame, 1, "Color", self.bar_color)
        self._palette_row(frame, 2, self.bar_color)
        self._alpha_row(frame, 3, "Opacity", self.bar_alpha)
        self._font_row(frame, 4, "Text size", self.bar_font)
        return frame

    # ---- wait note panel ----
    def _wait_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", padx=14)
        tk.Checkbutton(frame, text="Show wait note", variable=self.show_wait,
                       command=self._wait_enable, bg=PANEL, fg=FG, selectcolor=PANEL,
                       activebackground=PANEL, font=("Segoe UI", 10),
                       highlightthickness=0, bd=0).grid(
                       row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 2))
        pos = tk.Frame(frame, bg=PANEL)
        pos.grid(row=1, column=0, columnspan=3, sticky="w", padx=10)
        tk.Label(pos, text="Position:", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).grid(row=0, column=0, padx=(0, 8))
        for col, (label, val) in enumerate([("Bottom (taskbar)", "bottom"), ("Top", "top")]):
            tk.Radiobutton(pos, text=label, variable=self.wait_position, value=val,
                           bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
                           font=("Segoe UI", 9), highlightthickness=0, bd=0).grid(
                           row=0, column=col + 1, padx=(0, 10))
        self._color_row(frame, 2, "Color", self.wait_color)
        self._palette_row(frame, 3, self.wait_color)
        self._alpha_row(frame, 4, "Opacity", self.wait_alpha)
        self._font_row(frame, 5, "Text size", self.wait_font)
        return frame

    # ---- generic rows ----
    def _color_row(self, parent: tk.Frame, row: int, label: str, var: tk.StringVar):
        fr = tk.Frame(parent, bg=PANEL)
        fr.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=1)
        tk.Label(fr, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        tk.Button(fr, text="Pick color", command=lambda: self._pick(var, self._swatch(var, fr)),
                  bg=FIELD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=10,
                  activebackground="#3a3a58").grid(row=0, column=1)
        self._swatch(var, fr).grid(row=0, column=2, padx=(8, 4))
        tk.Label(fr, textvariable=var, bg=PANEL, fg=DIM,
                 font=("Consolas", 9)).grid(row=0, column=3, sticky="w", padx=(0, 4))

    def _swatch(self, var: tk.StringVar, parent: tk.Frame):
        sw = tk.Label(parent, text="   ", bg=var.get(), width=3)
        var.trace_add("write", lambda *a: sw.config(bg=var.get()))
        return sw

    def _palette_row(self, parent: tk.Frame, row: int, var: tk.StringVar):
        fr = tk.Frame(parent, bg=PANEL)
        fr.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=1)
        for color in PALETTE:
            s = tk.Label(fr, text="  ", bg=color, cursor="hand2")
            s.grid(row=0, column=fr.grid_size()[0], padx=2)
            s.bind("<Button-1>", lambda e, c=color: var.set(c))

    def _alpha_row(self, parent: tk.Frame, row: int, label: str, var: tk.DoubleVar):
        fr = tk.Frame(parent, bg=PANEL)
        fr.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=1)
        tk.Label(fr, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        tk.Scale(fr, from_=0.0, to=1.0, resolution=0.05, orient="horizontal",
                 variable=var, bg=PANEL, fg=FG, highlightthickness=0, bd=0,
                 troughcolor=FIELD, activebackground=ACCENT, length=150,
                 font=("Segoe UI", 8)).grid(row=0, column=1)

    def _font_row(self, parent: tk.Frame, row: int, label: str, var: tk.IntVar):
        fr = tk.Frame(parent, bg=PANEL)
        fr.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=3)
        tk.Label(fr, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        tk.Spinbox(fr, from_=8, to=28, textvariable=var, width=4, bg=FIELD, fg=FG,
                   buttonbackground="#33334a", relief="flat",
                   font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w")

    def _pick(self, var: tk.StringVar, swatch: tk.Label):
        _, color = colorchooser.askcolor(color=var.get(), title="Pick a color")
        if color:
            hexc = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}".upper()
            var.set(hexc)
            swatch.config(bg=hexc)

    def _bar_enable(self):
        state = "normal" if self.show_bar.get() else "disabled"
        for row_ in self.bar_rows.winfo_children():
            self._set_state(row_, state)

    def _wait_enable(self):
        state = "normal" if self.show_wait.get() else "disabled"
        for row_ in self.wait_rows.winfo_children():
            self._set_state(row_, state)

    def _set_state(self, widget: tk.Widget, state: str):
        for child in widget.winfo_children():
            if isinstance(child, (tk.Button, tk.Scale, tk.Spinbox, tk.Entry,
                                  tk.Radiobutton, tk.Checkbutton)):
                child.config(state=state)
            else:
                self._set_state(child, state)

    # ------------------------------------------------------------ actions

    def _collect(self):
        """Build a settings dict from the current form state, or return a
        (None, error_msg) tuple when something is invalid."""
        hotkeys = []
        for row in self.rows:
            hk = cfg.normalize_hotkey(row["hk"].get())
            if not hk:
                return None, (f"Invalid hotkey: \"{row['hk'].get()}\" "
                              f"(need at least one key + a modifier).")
            label = row["label"].get().strip() or row["mode"].get().capitalize()
            action = {"hotkey": hk, "label": label,
                      "mode": row["mode"].get(),
                      "enabled": bool(row["on"].get())}
            if row["mode"].get() == "translate":
                action["target"] = row["target"].get().strip() or "English"
            elif row["mode"].get() == "custom":
                action["prompt"] = row["prompt"].get().strip()
            hotkeys.append(action)

        seen = set()
        for a in hotkeys:
            if a["hotkey"] in seen:
                return None, f"Duplicate hotkey: {a['hotkey']}"
            seen.add(a["hotkey"])

        if not hotkeys:
            return None, "Add at least one hotkey action."

        s = {
            "translate_target": "English",
            "hotkeys": hotkeys,
            "show_bar": self.show_bar.get(),
            "bar_color": self.bar_color.get(),
            "bar_alpha": round(self.bar_alpha.get(), 2),
            "bar_font_size": int(self.bar_font.get()),
            "show_wait": self.show_wait.get(),
            "wait_position": self.wait_position.get(),
            "wait_color": self.wait_color.get(),
            "wait_alpha": round(self.wait_alpha.get(), 2),
            "wait_font_size": int(self.wait_font.get()),
        }
        return s, None

    def _reset(self):
        """Fill the whole window with the stealth / default profile."""
        p = cfg.stealth_profile()
        self.show_bar.set(p["show_bar"])
        self.bar_color.set(p["bar_color"])
        self.bar_alpha.set(p["bar_alpha"])
        self.bar_font.set(p["bar_font_size"])
        self.show_wait.set(p["show_wait"])
        self.wait_position.set(p["wait_position"])
        self.wait_color.set(p["wait_color"])
        self.wait_alpha.set(p["wait_alpha"])
        self.wait_font.set(p["wait_font_size"])

        self.clear_rows()
        for item in p["hotkeys"]:
            self._add_row(item)

        self._bar_enable()
        self._wait_enable()
        self.body_canvas.yview_moveto(0)
        self.status.config(text="Reset applied: only Solve is on, search bar "
                                "off, wait note barely visible (stealth).",
                           fg=GREEN)

    def _submit(self):
        s, err = self._collect()
        if err:
            self._msg(err, error=True)
            return

        run = self.run_after.get()
        if run:
            confirm = ("Apply these settings and start the tool right now?\n\n"
                       "It runs invisibly in the background. If it's already "
                       "running it will be restarted with the new settings.")
        else:
            confirm = ("Apply these settings WITHOUT starting the tool?\n\n"
                       "Any running instance will be stopped. You can launch "
                       "it later with start_hidden.vbs.")

        if not messagebox.askyesno("Submit changes", confirm):
            return

        cfg.save_settings(s)
        if run:
            restart_tool()
            self._msg("Saved. Tool is starting...")
        else:
            _kill_tool()
            self._msg("Saved. Tool stopped -- launch it with start_hidden.vbs "
                      "when you're ready.")
        self.root.update_idletasks()
        self.root.after(350, self.root.destroy)

    def _msg(self, text: str, error: bool = False):
        self.status.config(text=text, fg=RED if error else GREEN)
        self.root.update_idletasks()

    def center_window(self, w: int, h: int):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")


if __name__ == "__main__":
    try:
        SettingsApp(tk.Tk()).root.mainloop()
    except KeyboardInterrupt:
        pass
