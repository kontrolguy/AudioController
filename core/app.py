import pygame
import time
from display.renderer import Renderer
import json

from services.homeassistant import HomeAssistant
from screens.clock import ClockScreen
from screens.spotify import SpotifyScreen
from screens.hass import HassScreen
from display.volume import draw_volume
from hardware.input import handle
from core.state import state


class AudioHubApp:

    def __init__(self):

        self.renderer = Renderer()

        self.clock_screen = ClockScreen()
        self.spotify_screen = SpotifyScreen()
        self.hass_screen = HassScreen()
        with open("config.json") as f:
          config = json.load(f)


        self.ha = HomeAssistant(
         config["homeassistant"]["url"],
         config["homeassistant"]["token"]
        )


        state.hass_items = config["devices"]
        self.running = True


    def update_screen(self):

        if state.screen == "clock":

            self.clock_screen.draw(
                self.renderer.screen
            )
        if state.volume_visible:

             draw_volume(
                 self.renderer.screen,
                state.volume
             )

        elif state.screen == "spotify":

            self.spotify_screen.draw(
                self.renderer.screen,
                state.spotify_progress
            )


        elif state.screen == "hass":

            self.hass_screen.draw(
            self.renderer.screen,
            state.hass_items,
            state.hass_selected,
            self.ha
        )

    if state.volume_visible:

        draw_volume(
            self.renderer.screen,
            state.volume
        )


        if time.time() - state.volume_timer > 2:

            state.volume_visible = False

    def run(self):

        while self.running:

            events = pygame.event.get()


            for event in events:

                if event.type == pygame.QUIT:
                    self.running = False


            handle(events)

            state.update()

            self.renderer.clear()

            self.update_screen()

            self.renderer.update()


        pygame.quit()