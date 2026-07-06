# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

HoverX is a Windows-only PyQt6 desktop app: a small always-on-top floating
pill that expands on hover into playback controls (play/pause/next/prev,
volume) for whatever's currently playing system-wide, via the Windows media
session (SMTC) — the same mechanism the OS volume flyout and hardware media
keys use. Ships with a tray icon and a self-updating exe.

## Commands

```
pip install -r requirements.txt
python -m hoverx.app          # run from source (or `py -3 -m hoverx.app` if
                               # `python` isn't on PATH)

pyinstaller HoverX.spec           # build HoverX.exe
pyinstaller HoverX_updater.spec   # build HoverX_updater.exe (separate helper)
```

There is no automated test suite in this repo. Verifying a change means
actually running the app and exercising the affected flow (hover/expand,
drag, volume, track metadata, or the updater).

## Architecture

### UI: shell vs. content split (`hoverx/ui/`)

`widget.py`'s `FloatingWidget` is the top-level always-on-top translucent
window. It owns only: window flags/geometry, the collapsed-dot painting, the
expand/collapse animation, and drag handling. It does **not** build any of
the visible controls itself — it creates one `ControlsPanel` (from
`controls_panel.py`) as a child and wires that panel's signals
(`play_pause_clicked`, `volume_changed`, etc.) to the `controller`.

Two non-obvious things worth knowing before touching this code:

- **`ControlsPanel` must set `Qt.WidgetAttribute.WA_StyledBackground`.** A
  custom `QWidget` subclass (as opposed to a plain `QWidget` instance)
  silently ignores its stylesheet's `background`/`border-radius` without this
  attribute. Missing it once made the panel fully transparent *and*
  click-through (the top-level window is a translucent layered window, and
  Windows does alpha-based hit-testing on those — unpainted pixels don't
  receive clicks, which is why dragging broke at the same time as the visual
  bug).
- **The hover expand/collapse state is a poll-backed state machine, not pure
  enter/leave events.** `FloatingWidget` tracks an explicit `_expanded` bool
  and runs a ~120ms `QTimer` (`_check_hover`) that force-collapses based on
  the *actual* cursor position, independent of Qt's `enterEvent`/`leaveEvent`.
  This exists because Windows' native leave notification requires
  `TrackMouseEvent` to have been armed by a prior mouse-move inside the
  window; fast cursor movement can skip that arming entirely, so
  `leaveEvent` silently never fires and the widget gets stuck expanded.
  Don't "simplify" this back to enter/leave-only — that's the bug it fixes.
  `_on_anim_finished` is a single persistent slot (not per-call
  connect/disconnect) specifically so re-triggering expand/collapse mid
  animation can't leave a stale handler that fires at the wrong time.

`ui/marquee_label.py`'s `MarqueeLabel` renders normally when text fits, and
paints a manually-scrolled, seamlessly-looping copy when it doesn't (used for
long titles/artists instead of eliding with "..."). `setMarqueeText()` is a
no-op if the text hasn't actually changed — the 1s track-info poll
re-reports the same title every tick, and resetting the scroll offset on
every one of those calls is what previously made it look like it was
snapping back to the start instead of looping.

### Controller layer (`hoverx/controller/`)

`base.py` defines the `MediaController` interface (`play_pause`, `next`,
`previous`, `get_track_info`, `is_playing`, `get_volume`, `set_volume`). Two
implementations, chosen once in `app.py:main()`:

- `windows_smtc.WindowsSMTCController` — the real one. WinRT's SMTC API is
  async-only, so it runs its own asyncio event loop on a background thread
  and bridges every call through `run_coroutine_threadsafe`. **Volume is the
  system master volume via `pycaw`**, not per-app — SMTC itself has no
  volume API, and matching an SMTC session to a specific audio session/app
  was judged too fragile to be worth it. Note `AudioUtilities.GetSpeakers()`
  returns a wrapper whose `.EndpointVolume` *is already* the
  `POINTER(IAudioEndpointVolume)` — don't try to `.Activate(...)` it again.
- `dummy.DummyController` — in-memory stub, used as the fallback if
  `WindowsSMTCController()` fails to construct (e.g. not on Windows, or WinRT
  unavailable), so the UI is still runnable/demoable everywhere.

`WindowsSMTCController` does **not** formally inherit `MediaController` (it
matches the interface by duck typing) — don't go looking for that
inheritance relationship.

### Auto-updater (`hoverx/updater/`, `hoverx/app.py`, `update.json`)

`checker.py` fetches `update.json` from `raw.githubusercontent.com/.../main/`
(always the `main` branch, regardless of what's installed) and compares its
`"version"` against `hoverx/version.py`'s `__version__`. If newer,
`downloader.py` downloads the `"url"` (a GitHub Release asset) with
integrity verification (checks downloaded bytes against `Content-Length`,
cleans up partial files on any failure) and retry-with-backoff
(`retry.py`). `app.py` then hands off to the separate `HoverX_updater.exe`
(built from `updater/helper.py`) via `trigger_update()`, which does a hard
`os._exit(0)` — the updater process does the actual file swap (old exe →
`.bak`, new exe → real name) after the main process has fully exited, since
Windows can't replace a running exe's file in place.

**The release workflow (`.github/workflows/release.yml`) is what keeps
`update.json`/`version.py` truthful.** Pushing a tag `vX.Y.Z` to `main`
builds both exes, *derives the version from the tag* (not from whatever's
committed in `version.py`), overwrites `version.py`/`update.json` to match,
commits that back to `main`, and publishes the GitHub Release with both
exes attached at the URL `update.json` now points to. In other words: the
tag is the actual source of truth at release time, even though we also keep
`version.py`/`update.json` manually in sync in the same commit that bumps
the version, for immediate local consistency before the tag is pushed.

The exes are **not currently code-signed** — Windows SmartScreen / Smart App
Control will warn or block on fresh installs. There's no free option for
this (see README's note); a SignPath Foundation application is the
in-progress path if that comes up again.

`HoverX.spec`/`HoverX_updater.spec` are intentionally tracked in git (do not
re-add `*.spec` to `.gitignore` — that was a prior mistake that would make
CI builds fail, since the spec files wouldn't exist on the runner). `build/`
and `dist/` (PyInstaller output) stay gitignored.

## Branching / release process

`main` is always releasable. Enhancements/fixes get a short-lived
`feature/<name>` or `fix/<name>` branch off `main`, merged back and deleted
immediately once done — don't leave merged branches sitting around. A
release is just a version bump (`hoverx/version.py` + `update.json`) plus
`git tag vX.Y.Z && git push origin vX.Y.Z`; the GitHub Actions workflow
above handles the rest.
