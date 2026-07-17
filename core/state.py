import time


class State:
    def __init__(self):
        self.screen = "clock"

        # Volume
        self.volume = 50
        self.volume_visible = False
        self.volume_last_change = 0.0

        # Spotify
        self.spotify_playing = False
        self.spotify_title = ""
        self.spotify_artist = ""
        self.spotify_album = ""
        self.spotify_track_id = ""
        self.spotify_artwork_path = ""
        self.spotify_position_ms = 0
        self.spotify_duration_ms = 0
        self.spotify_position_timestamp = 0.0
        self.spotify_progress = 0.0
        self.spotify_device_name = ""
        self.spotify_error = ""

        # Home Assistant
        self.hass_items = []
        self.hass_selected = 0

    def show_volume(self):
        self.volume_visible = True
        self.volume_last_change = time.monotonic()

    def update(self):
        if (
            self.volume_visible
            and time.monotonic() - self.volume_last_change > 2
        ):
            self.volume_visible = False

        position = self.spotify_position_ms

        if (
            self.spotify_playing
            and self.spotify_position_timestamp > 0
        ):
            elapsed = (
                time.monotonic()
                - self.spotify_position_timestamp
            )
            position += int(max(0.0, elapsed) * 1000)

        if self.spotify_duration_ms > 0:
            position = min(
                position,
                self.spotify_duration_ms,
            )

            self.spotify_progress = max(
                0.0,
                min(
                    1.0,
                    position / self.spotify_duration_ms,
                ),
            )
        else:
            self.spotify_progress = 0.0


state = State()
