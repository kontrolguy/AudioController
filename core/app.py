import json

import pygame

from core.state import state
from display.renderer import Renderer
from display.volume import draw_volume
from hardware.input import handle
from screens.clock import ClockScreen
from screens.hass import HassScreen
from screens.spotify import SpotifyScreen
from services.homeassistant import HomeAssistant
from services.spotify import (
    LibrespotProcess,
    SpotifyService,
)


class AudioHubApp:
    def __init__(self):
        self.renderer = Renderer()

        self.clock_screen = ClockScreen()
        self.spotify_screen = SpotifyScreen()
        self.hass_screen = HassScreen()

        with open(
            "config.json",
            encoding="utf-8",
        ) as file:
            config = json.load(file)

        self.ha = HomeAssistant(
            config["homeassistant"]["url"],
            config["homeassistant"]["token"],
        )

        state.hass_items = config["devices"]

        self.librespot = LibrespotProcess()
        self.librespot.start()

        self.spotify_service = SpotifyService()
        self.spotify_service.start()

        self.spotify_was_playing = False
        self.running = True

    def sync_spotify_state(self):
        spotify = self.spotify_service.get_state()

        started_playing = (
            spotify.playing
            and not self.spotify_was_playing
        )

        self.spotify_was_playing = (
            spotify.playing
        )

        state.spotify_playing = spotify.playing
        state.spotify_title = spotify.title
        state.spotify_artist = spotify.artist
        state.spotify_album = spotify.album
        state.spotify_track_id = spotify.track_id
        state.spotify_artwork_path = (
            spotify.artwork_path
        )
        state.spotify_position_ms = (
            spotify.position_ms
        )
        state.spotify_duration_ms = (
            spotify.duration_ms
        )
        state.spotify_position_timestamp = (
            spotify.position_timestamp
        )
        state.spotify_device_name = (
            spotify.device_name
        )
        state.spotify_error = spotify.error

        if spotify.volume_percent >= 0:
            state.volume = (
                spotify.volume_percent
            )

        if started_playing:
            state.screen = "spotify"

    def update_screen(self):
        if state.screen == "clock":
            self.clock_screen.draw(
                self.renderer.screen
            )

        elif state.screen == "spotify":
            self.spotify_screen.draw(
                self.renderer.screen,
                state.spotify_progress,
            )

        elif state.screen == "hass":
            self.hass_screen.draw(
                self.renderer.screen,
                state.hass_items,
                state.hass_selected,
                self.ha,
            )

        if state.volume_visible:
            draw_volume(
                self.renderer.screen,
                state.volume,
            )

    def run(self):
        try:
            while self.running:
                events = pygame.event.get()

                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False

                handle(
                    events,
                    spotify_service=(
                        self.spotify_service
                    ),
                    home_assistant=self.ha,
                )

                self.sync_spotify_state()
                state.update()

                self.renderer.clear()
                self.update_screen()
                self.renderer.update()

        finally:
            self.spotify_service.stop()
            self.librespot.stop()
            pygame.quit()
