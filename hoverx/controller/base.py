class MediaController:
    """
    Abstract-ish base controller.
    UI depends on this, not on OS-specific implementations.
    """

    def play_pause(self):
        raise NotImplementedError("Subclasses must implement play_pause method")
    
    def next(self):
        raise NotImplementedError("Subclasses must implement next method")
    
    def previous(self):
        raise NotImplementedError("Subclasses must implement previous method")
    
    def get_track_info(self):
        """
        Returns (title, artist)
        """
        raise NotImplementedError("Subclasses must implement get_track_info method")
    
    def is_playing(self) -> bool:
        raise NotImplementedError("Subclasses must implement is_playing method")