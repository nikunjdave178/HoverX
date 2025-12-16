from hoverx.controller.base import MediaController


class DummyController(MediaController):
    def __init__(self):
        self.is_playing = False
        self.track_index = 1

    def play_pause(self):
        self.is_playing = not self.is_playing
        print("PLAY" if self.is_playing else "PAUSE")

    def next(self):
        self.track_index += 1
        print("NEXT")

    def previous(self):
        self.track_index = max(1, self.track_index - 1)
        print("PREVIOUS")

    def get_track_info(self):
        return f"Track {self.track_index}", "Dummy Controller"
