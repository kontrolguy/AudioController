import pygame
import math


class SpotifyScreen:


    def draw(self,surface,progress):


        pygame.draw.arc(
            surface,
            (30,255,120),
            (40,40,320,320),
            0,
            progress*math.pi*2,
            10
        )


        pygame.draw.circle(
            surface,
            (30,30,30),
            (200,200),
            110
        )


        font=pygame.font.SysFont(
            None,
            28
        )


        song=font.render(
            "Artist - Song",
            True,
            (255,255,255)
        )


        surface.blit(
            song,
            (115,195)
        )