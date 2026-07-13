import pygame
from core.state import state


def handle(events):


    for e in events:


        if e.type==pygame.KEYDOWN:


            # óra
            if e.key==pygame.K_1:
                state.screen="clock"


            # spotify
            if e.key==pygame.K_2:
                state.screen="spotify"


            # HA
            if e.key==pygame.K_3:
                state.screen="hass"



            # encoder fel
            if e.key==pygame.K_UP:

                state.hass_selected-=1


            # encoder le
            if e.key==pygame.K_DOWN:

                state.hass_selected+=1



            # encoder nyomás
            if e.key==pygame.K_RETURN:

                print(
                    "Selected:",
                    state.hass_items[state.hass_selected]
                )