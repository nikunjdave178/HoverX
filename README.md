# HoverX

A small, always-on-top floating media widget for Windows. It sits as a
compact pill on your screen and expands on hover into playback controls for
whatever's currently playing system-wide (Spotify, browser tabs, any app
that reports to Windows' media session), with a volume slider — no need to
alt-tab back to the source app just to skip a track or adjust volume.

## Features

- Hover-to-expand floating widget, draggable anywhere on screen
- Play/pause, next, previous — controls the active Windows media session
  (via SMTC, the same system used by the Windows volume flyout / media keys)
- Vertical volume slider with a live percentage readout; scroll the mouse
  wheel anywhere over the expanded widget to adjust volume
- Track title/artist that scroll in place when too long to fit
- System tray icon (show/hide/exit)
- Built-in auto-updater that checks for new releases and updates in place

## Installing

Grab the latest `HoverX.exe` from the
[Releases page](https://github.com/nikunjdave178/HoverX/releases) and run
it — no installer, it's a single portable executable. It adds nothing to
your system (no registry entries, no startup entries); to remove it, just
delete the exe.

> **Note:** the executable isn't yet code-signed, so Windows SmartScreen /
> Smart App Control may warn about it on first run. See
> [Releases](https://github.com/nikunjdave178/HoverX/releases) for the
> current signing status.

## Running from source

Requires Python 3.11+ on Windows.

```
pip install -r requirements.txt
python -m hoverx.app
```

## Building

PyInstaller builds both the app and its updater helper from the checked-in
spec files:

```
pyinstaller HoverX.spec
pyinstaller HoverX_updater.spec
```

## Privacy

HoverX does not collect, transmit, or store any user data. Media track
info is read locally from the Windows media session API to display in the
widget and never leaves your machine. The only file it writes is a local
diagnostic log (`%TEMP%\hoverx.log`) used for troubleshooting.

## Contributing

Issues and pull requests are welcome — use the
[issue tracker](https://github.com/nikunjdave178/HoverX/issues).

## License

[MIT](LICENSE)
