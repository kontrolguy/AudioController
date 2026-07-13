import pygame
import datetime


class ClockScreen:


    def draw(self,surface):

        font = pygame.font.SysFont(
            None,
            70
        )

        small = pygame.font.SysFont(
            None,
            30
        )


        now=datetime.datetime.now()


        t=font.render(
            now.strftime("%H:%M"),
            True,
            (255,255,255)
        )


        d=small.render(
            now.strftime("%d %B"),
            True,
            (180,180,180)
        )


        surface.blit(
            t,
            (120,130)
        )


        surface.blit(
            d,
            (140,210)
        )