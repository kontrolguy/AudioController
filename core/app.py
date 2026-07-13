import pygame

from display.renderer import Renderer

from screens.clock import ClockScreen
from screens.spotify import SpotifyScreen
from screens.hass import HassScreen

from hardware.input import handle
from core.state import state


class AudioHubApp:

    def __init__(self):

        self.renderer = Renderer()

        self.clock_screen = ClockScreen()
        self.spotify_screen = SpotifyScreen()
        self.hass_screen = HassScreen()

        self.running = True


    def update_screen(self):

        if state.screen == "clock":

            self.clock_screen.draw(
                self.renderer.screen
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
                state.hass_selected
            )


    def run(self):

        while self.running:

            events = pygame.event.get()


            for event in events:

                if event.type == pygame.QUIT:
                    self.running = False


            handle(events)

            self.renderer.clear()

            self.update_screen()

            self.renderer.update()


        pygame.quit()