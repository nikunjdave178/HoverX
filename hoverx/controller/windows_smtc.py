import asyncio
import threading

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager
)


class WindowsSMTCController:
    def __init__(self):
        self._manager = None
        self._playing = False
        self._last_title = ""
        self._last_artist = ""

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

    # ---------- Core async logic ----------
    async def _ensure_manager(self):
        if not self._manager:
            self._manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()

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
        except Exception:
            pass

        return self._last_title, self._last_artist

    def is_playing(self) -> bool:
        return self._playing

    def play_pause(self):
        self._run_async(self._toggle())

    async def _toggle(self):
        await self._ensure_manager()
        session = self._manager.get_current_session()
        if session:
            await session.try_toggle_play_pause_async()

    def next(self):
        self._run_async(self._next())

    async def _next(self):
        await self._ensure_manager()
        session = self._manager.get_current_session()
        if session:
            await session.try_skip_next_async()

    def previous(self):
        self._run_async(self._previous())

    async def _previous(self):
        await self._ensure_manager()
        session = self._manager.get_current_session()
        if session:
            await session.try_skip_previous_async()
