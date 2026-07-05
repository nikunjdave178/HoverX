import asyncio
import threading

import comtypes
from pycaw.pycaw import AudioUtilities
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager
)

from hoverx.logging_utils import log


class WindowsSMTCController:
    def __init__(self):
        self._manager = None
        self._playing = False
        self._last_title = ""
        self._last_artist = ""
        self._last_volume = 50
        self._volume_iface = None

        # Async loop in background thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True
        )
        self._thread.start()

        # Initialize manager
        self._run_async(self._ensure_manager())

    # ---------- Async infra ----------
    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def shutdown(self):
        """Stops the background asyncio loop so its thread can exit."""
        self._loop.call_soon_threadsafe(self._loop.stop)

    # ---------- Core async logic ----------
    async def _ensure_manager(self):
        if not self._manager:
            self._manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()

    async def _run_session_action(self, method_name: str):
        """Shared "ensure manager -> get session -> call try_X_async" path
        used by play_pause/next/previous."""
        await self._ensure_manager()
        session = self._manager.get_current_session()
        if not session:
            return
        try:
            await getattr(session, method_name)()
        except Exception as e:
            log(f"SMTC action {method_name} failed: {e}")

    async def _poll_track_info(self):
        await self._ensure_manager()

        session = self._manager.get_current_session()
        if not session:
            return

        playback = session.get_playback_info()
        status = playback.playback_status.name

        if status not in ("PLAYING", "PAUSED"):
            return

        props = await session.try_get_media_properties_async()

        self._last_title = getattr(props, "title", "") or ""
        self._last_artist = getattr(props, "artist", "") or ""
        self._playing = status == "PLAYING"

    # ---------- Public (sync) API ----------
    def get_track_info(self):
        future = self._run_async(self._poll_track_info())
        try:
            future.result(timeout=0.5)
        except Exception as e:
            log(f"get_track_info failed: {e}")

        return self._last_title, self._last_artist

    def is_playing(self) -> bool:
        return self._playing

    def play_pause(self):
        self._run_async(self._run_session_action("try_toggle_play_pause_async"))

    def next(self):
        self._run_async(self._run_session_action("try_skip_next_async"))

    def previous(self):
        self._run_async(self._run_session_action("try_skip_previous_async"))

    # ---------- Volume (system master volume via pycaw) ----------
    # SMTC sessions expose no volume API - volume is a separate Windows Core
    # Audio concept. We control the system master volume rather than trying
    # to match the SMTC session to a specific per-app audio session, which
    # would be far more fragile.
    def _get_volume_endpoint(self):
        if self._volume_iface is not None:
            return self._volume_iface
        try:
            comtypes.CoInitialize()
        except Exception:
            pass  # already initialized on this thread - fine
        try:
            self._volume_iface = AudioUtilities.GetSpeakers().EndpointVolume
        except Exception as e:
            log(f"Volume endpoint init failed: {e}")
            self._volume_iface = None
        return self._volume_iface

    def get_volume(self) -> int:
        iface = self._get_volume_endpoint()
        if iface is None:
            return self._last_volume
        try:
            self._last_volume = round(iface.GetMasterVolumeLevelScalar() * 100)
        except Exception as e:
            log(f"get_volume failed: {e}")
        return self._last_volume

    def set_volume(self, value: int):
        value = max(0, min(100, value))
        self._last_volume = value

        iface = self._get_volume_endpoint()
        if iface is None:
            return
        try:
            iface.SetMasterVolumeLevelScalar(value / 100, None)
        except Exception as e:
            log(f"set_volume failed: {e}")
