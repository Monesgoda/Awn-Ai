# Changelog

All notable changes to **StealthClip** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/).

## [1.4.0] — 2026-08-28

### Added
- **Multiple hotkeys** — each hotkey is bound to its own action/mode
  (`solve`, `explain`, `translate`, `custom` you define) instead of one fixed
  hotkey.
- **Custom action** — a 4th mode that uses any prompt you write.
- **Reset button** in settings — applies the stealth default profile: only
  *Solve* is enabled, the search bar is off, and the wait note stays on but
  is a faint, barely-visible pale white in the taskbar corner.
- **"Start the tool now after saving" checkbox** next to Submit — tick it to
  immediately (re)start the background tool with the new settings, or untick
  it to only save & stop and launch later with `start_hidden.vbs`.
- Compact settings window that scrolls internally instead of being tall.

### Changed
- Main script renamed `proxy_Network.py` → `main.py` (clearer name; launchers
  and docs updated).
- Submit button now saves and closes the window (no auto-restart) unless the
  new run-after-save checkbox is ticked.

## [1.3.0] — 2026-08-28

### Added
- **Auto-restart on save**: saving settings now stops and relaunches the
  background tool automatically, so changes apply instantly (no manual
  restart).
- **Color is now actually visible**: the bar color is displayed (was hidden
  before because the chosen color doubled as the transparent key).
- **Text size settings**: `bar_font_size` (bar text) and `wait_font_size`
  (wait note), configurable from 8 to 28.
- **Color presets** in the settings window + live preview / hex readout.

### Changed
- Settings window taller and reorganized; primary action renamed to
  *Save & Restart*.

## [1.2.0] — 2026-08-28

### Added
- **Settings window** (`settings_gui.py` + `start_settings.vbs`): a clean dark
  UI to configure everything without touching code.
- **AI modes**: pick how the answer is produced —
  *Solve* (direct answer, default), *Explain* (teach, no straight answer) and
  *Translate* (convert to a target language you choose).
- `settings.py` store: all options persist in `settings.json`.
- Toggle for the search bar (hide it completely, hotkey-only).
- Toggle for the wait note (off / on), with its own color, opacity and
  position (bottom taskbar / top of screen).

### Changed
- The main script now reads live settings instead of hard-coded values.
- Bar color, wait-note color and both opacities are user-selectable.

## [1.1.0] — 2026-08-28

### Added
- **Instant clipboard mode**: pressing `Ctrl+Alt+A` now sends the clipboard
  text directly to the AI — no bar, no Enter key. Faster and more discreet.
- `VERSION` constant (sent as `User-Agent` on local HTTP requests:
  `StealthClip/1.1.0`).
- `setup.bat` one-click installer and `stop.bat` for non-programmer users.
- This changelog + full `REPORT.md`.

### Changed
- Manual input bar now only appears when the clipboard is empty.
- Removed the bright "Processing..." status on submit (stealth).
- Removed the "Done!" success popup — the taskbar "wait" note is the only
  feedback.
- Removed window backgrounds entirely via per-pixel transparency.

## [1.0.0] — 2026-08-28

### Added
- Initial release: background clipboard AI assistant.
- Global hotkey `Ctrl+Alt+A`; hidden `pythonw` launcher (`start_hidden.vbs`).
- Near-invisible bottom bar + animated "wait" note on the taskbar.
- Local-only backend to `127.0.0.1` (ports `30231` / `8051`) with one-shot
  `opencode run` fallback.
- ANSI/fence stripping for copy-ready output.