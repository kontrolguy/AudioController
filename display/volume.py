import pygame


def draw_volume(surface, volume):

    # kék kör
    pygame.draw.arc(
        surface,
        (0,150,255),
        (40,40,320,320),
        0,
        volume / 100 * 6.283,
        8
    )


    font = pygame.font.SysFont(
        None,
        55
    )


    text = font.render(
        f"{volume}%",
        True,
        (0,150,255)
    )


    surface.blit(
        text,
        (165,175)
    )