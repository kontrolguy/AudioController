import pygame
import time

from core.state import state


def handle(events):

    for e in events:

        if e.type != pygame.KEYDOWN:
            continue


        # Képernyő váltás

        if e.key == pygame.K_1:
            state.screen = "clock"


        elif e.key == pygame.K_2:
            state.screen = "spotify"


        elif e.key == pygame.K_3:
            state.screen = "hass"



        # Hangerő

        elif e.key == pygame.K_RIGHT:

            state.volume = min(
                100,
                state.volume + 5
            )

            state.show_volume()



        elif e.key == pygame.K_LEFT:

            state.volume = max(
                0,
                state.volume - 5
            )

            state.show_volume()



        # Home Assistant navigáció

        elif state.screen == "hass":

            if e.key == pygame.K_DOWN:

                state.hass_selected += 1

                if state.hass_selected >= len(state.hass_items):
                    state.hass_selected = 0


            elif e.key == pygame.K_UP:

                state.hass_selected -= 1

                if state.hass_selected < 0:
                    state.hass_selected = len(state.hass_items)-1


            elif e.key == pygame.K_RETURN:

                if len(state.hass_items) > 0:

                    item = state.hass_items[
                        state.hass_selected
                    ]

                    print(
                        "Selected:",
                        item["name"]
                    )

                    if item["type"] in [
                        "light",
                        "switch",
                        "fan"
                    ]:

                        print(
                            "Toggle:",
                            item["entity_id"]
                        )