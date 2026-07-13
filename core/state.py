class State:

    def __init__(self):
        self.screen = "clock"

        self.spotify_playing = True
        self.spotify_progress = 0.35

        self.hass_items = [
            "Nappali lampa",
            "Klima",
            "Homerseklet",
            "Redony"
        ]

        self.hass_selected = 0


state = State()