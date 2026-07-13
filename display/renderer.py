import pygame


class Renderer:

    def __init__(self, width=400, height=400):

        pygame.init()

        self.screen = pygame.display.set_mode(
            (width,height)
        )

        self.clock = pygame.time.Clock()

        self.volume_timer = 0


    def clear(self):

        self.screen.fill(
            (15,15,15)
        )


    def update(self):

        pygame.display.flip()

        self.clock.tick(60)