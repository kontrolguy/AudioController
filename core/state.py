import time


class State:

    def __init__(self):

        self.screen = "clock"

        # hangerő
        self.volume = 50
        self.volume_visible = False
        self.volume_last_change = 0

        # Spotify
        self.spotify_progress = 0.35

        # HA
        self.hass_items = []
        self.hass_selected = 0


    def show_volume(self):

        self.volume_visible = True
        self.volume_last_change = time.time()


    def update(self):

        if self.volume_visible:

            if time.time() - self.volume_last_change > 2:

                self.volume_visible = False



state = State()