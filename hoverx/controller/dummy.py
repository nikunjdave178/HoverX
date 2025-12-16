from hoverx.controller.base import MediaController

class DummyController(MediaController):
    def __init__(self):
        self.is_playing = False

    def play_pause(self):
        self.is_playing = not self.is_playing
        print("PLAY" if self.is_playing else "PAUSE")

    def next(self):
        print("NEXT")

    def previous(self):
        print("PREVIOUS")

    def get_track_info(self):
        return "No media", "Dummy controller"