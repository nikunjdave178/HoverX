from hoverx.controller.base import MediaController


class DummyController(MediaController):
    def __init__(self):
        self._playing = False
        self.track_index = 1

    def play_pause(self):
        self._playing = not self._playing
        print("PLAY" if self._playing else "PAUSE")

    def next(self):
        self.track_index += 1
        print("NEXT")

    def previous(self):
        self.track_index = max(1, self.track_index - 1)
        print("PREVIOUS")

    def get_track_info(self):
        return f"Track {self.track_index}", "Dummy Controller"

    def is_playing(self) -> bool:
        return self._playing
