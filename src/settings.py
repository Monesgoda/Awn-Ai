"""
StealthClip settings store.

Central place for every user-tweakable option. Settings live in settings.json
next to this file; missing settings fall back to the DEFAULTS below. The main
script (main.py) reads them at startup, and settings_gui.py edits
them through a graphical window.

Since v1.4 the tool supports MULTIPLE hotkeys, each bound to its own action
(mode): for example Ctrl+Alt+A = Solve, Ctrl+Alt+E = Explain,
Ctrl+Alt+T = Translate, Ctrl+Alt+B = custom prompt. Every action has its own
hotkey which the user can change or extend freely.
"""

import json
import os

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json")

# Modifier names pynput understands (typed without the < > brackets).
MODIFIERS = {"ctrl", "control", "alt", "altgr", "shift", "win", "cmd", "super"}


def normalize_hotkey(combo) -> str:
    """Turn a friendly 'ctrl+alt+a' into pynput's '<ctrl>+<alt>+a'. Returns
    None when the combo has no non-modifier key (and therefore can't work).
    Idempotent: already-angled-bracket combos pass through unchanged."""
    if not combo:
        return None
    parts = [p.strip().strip("<>").lower()
             for p in str(combo).split("+") if p.strip()]
    if not parts:
        return None
    mods = [p for p in parts if p in MODIFIERS]
    keys = [p for p in parts if p not in MODIFIERS]
    if not keys:
        return None
    combo = "+".join("<" + m + ">" for m in mods)
    return combo + "+" + keys[0] if combo else keys[0]


def normalize_bindings(hotkeys) -> list:
    """Return a clean, de-duplicated list of action dicts (each with a valid
    normalized hotkey). Invalid and duplicate hotkeys are dropped."""
    seen = set()
    out = []
    for item in (hotkeys or []):
        if not isinstance(item, dict):
            continue
        hk = normalize_hotkey(item.get("hotkey"))
        if not hk or hk in seen:
            continue
        seen.add(hk)
        action = dict(item)
        action["hotkey"] = hk
        action.setdefault("enabled", True)
        out.append(action)
    return out


DEFAULT_HOTKEYS = [
    {"hotkey": "<ctrl>+<alt>+a", "label": "Solve", "enabled": True,
     "mode": "solve"},
    {"hotkey": "<ctrl>+<alt>+e", "label": "Explain", "enabled": True,
     "mode": "explain"},
    {"hotkey": "<ctrl>+<alt>+t", "label": "Translate", "enabled": True,
     "mode": "translate", "target": "English"},
    {"hotkey": "<ctrl>+<alt>+b", "label": "Quick Ask", "enabled": True,
     "mode": "custom",
     "prompt": ("You are a helpful assistant. Answer the user's request "
                "directly and concisely -- plain text, no markdown, no code "
                "fences, no headings.")},
]

DEFAULTS = {
    # Default fallback translation language (used when an action omits it)
    "translate_target": "English",
    # Every hotkey -> an action. "mode" is one of:
    #   solve | explain | translate | custom
    # translate actions may carry a "target" language; custom actions carry a
    # "prompt" that tells the AI how to behave. "enabled" (True/False) lets
    # you turn an action off without deleting its hotkey.
    "hotkeys": DEFAULT_HOTKEYS,

    # Search bar (appears when you press a hotkey with an empty clipboard)
    "show_bar": True,          # False = never show the bar, hotkey-only
    "bar_color": "#1a1a2e",    # bar background color (visible, tinted by alpha)
    "bar_alpha": 0.45,         # 0.0 invisible .. 1.0 solid
    "bar_font_size": 11,       # text size inside the bar entry

    # Wait note (the only feedback while working)
    "show_wait": True,         # False = no progress indicator at all
    "wait_position": "bottom", # "bottom" (on the taskbar) or "top"
    "wait_color": "#b0b0c0",   # note text color
    "wait_alpha": 0.60,        # 0.0 invisible .. 1.0 solid
    "wait_font_size": 10,      # text size of the wait note
}


def load_settings() -> dict:
    """Return the merged settings (stored values win over defaults)."""
    data = {k: (list(v) if isinstance(v, list) else v)
            for k, v in DEFAULTS.items()}
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            stored = json.load(f)
        if isinstance(stored, dict):
            for k in DEFAULTS:
                if k in stored:
                    data[k] = stored[k]
    except Exception:
        pass
    data["hotkeys"] = normalize_bindings(data.get("hotkeys"))
    if not data["hotkeys"]:
        data["hotkeys"] = DEFAULT_HOTKEYS
    return data


def stealth_profile() -> dict:
    """Return the stealth/default profile.

    What the "Reset" button applies: everything is locked except Solve, the
    search bar is off, and the wait note is ON but so faint it's only barely
    visible (a very pale white, low opacity) sitting in the bottom taskbar
    corner -- the person using it sees it, someone standing nearby won't.
    """
    hotkeys = [
        {"hotkey": "<ctrl>+<alt>+a", "label": "Solve", "enabled": True,
         "mode": "solve"},
        {"hotkey": "<ctrl>+<alt>+e", "label": "Explain", "enabled": False,
         "mode": "explain"},
        {"hotkey": "<ctrl>+<alt>+t", "label": "Translate", "enabled": False,
         "mode": "translate", "target": "English"},
        {"hotkey": "<ctrl>+<alt>+b", "label": "Quick Ask", "enabled": False,
         "mode": "custom",
         "prompt": ("You are a helpful assistant. Answer the user's request "
                    "directly and concisely -- plain text, no markdown, no code "
                    "fences, no headings.")},
    ]
    return {
        "translate_target": "English",
        "hotkeys": hotkeys,
        "show_bar": False,
        "bar_color": "#1a1a2e",
        "bar_alpha": 0.45,
        "bar_font_size": 11,
        "show_wait": True,
        "wait_position": "bottom",
        "wait_color": "#ffffff",
        "wait_alpha": 0.90,
        "wait_font_size": 11,
    }


def save_settings(settings: dict) -> None:
    """Persist the given settings dict to settings.json."""
    data = dict(DEFAULTS)
    kept = {k: v for k, v in settings.items() if k in DEFAULTS}
    if "hotkeys" in kept:
        kept["hotkeys"] = normalize_bindings(kept["hotkeys"])
    data.update(kept)
    if not data["hotkeys"]:
        data["hotkeys"] = DEFAULT_HOTKEYS
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    print(json.dumps(load_settings(), indent=2))
