import math
from pathlib import Path

import pygame

from core.state import state


class SpotifyScreen:
    def __init__(self):
        self.title_font = pygame.font.SysFont(
            None,
            30,
        )
        self.artist_font = pygame.font.SysFont(
            None,
            24,
        )
        self.small_font = pygame.font.SysFont(
            None,
            20,
        )
        self.icon_font = pygame.font.SysFont(
            None,
            82,
        )

        self.cached_path = ""
        self.cached_modified = 0.0
        self.cached_image = None

    @staticmethod
    def shorten(font, text, width):
        text = str(text)

        if font.size(text)[0] <= width:
            return text

        shortened = text

        while (
            shortened
            and font.size(
                shortened + "..."
            )[0] > width
        ):
            shortened = shortened[:-1]

        return shortened + "..."

    def load_artwork(self, path):
        if not path:
            self.cached_path = ""
            self.cached_modified = 0.0
            self.cached_image = None
            return None

        image_path = Path(path)

        if not image_path.exists():
            return None

        try:
            modified = image_path.stat().st_mtime

            if (
                path == self.cached_path
                and modified == self.cached_modified
            ):
                return self.cached_image

            image = pygame.image.load(
                str(image_path)
            ).convert_alpha()

            image = pygame.transform.smoothscale(
                image,
                (190, 190),
            )

            self.cached_path = path
            self.cached_modified = modified
            self.cached_image = image

            return image

        except (pygame.error, OSError):
            return None

    def draw(self, surface, progress=None):
        if progress is None:
            progress = state.spotify_progress

        progress = max(
            0.0,
            min(1.0, progress),
        )

        ring = pygame.Rect(
            28,
            28,
            344,
            344,
        )

        pygame.draw.arc(
            surface,
            (45, 45, 45),
            ring,
            0,
            math.tau,
            10,
        )

        if progress > 0:
            start = -math.pi / 2

            pygame.draw.arc(
                surface,
                (30, 140, 255),
                ring,
                start,
                start + progress * math.tau,
                10,
            )

        artwork = self.load_artwork(
            state.spotify_artwork_path
        )

        if artwork is not None:
            surface.blit(
                artwork,
                artwork.get_rect(
                    center=(200, 165)
                ),
            )
        else:
            pygame.draw.circle(
                surface,
                (32, 32, 32),
                (200, 165),
                95,
            )

            icon = self.icon_font.render(
                "♪",
                True,
                (115, 115, 115),
            )

            surface.blit(
                icon,
                icon.get_rect(
                    center=(200, 165)
                ),
            )

        title = self.shorten(
            self.title_font,
            state.spotify_title
            or "No playback",
            330,
        )

        artist = self.shorten(
            self.artist_font,
            state.spotify_artist
            or "Spotify Connect",
            330,
        )

        title_surface = self.title_font.render(
            title,
            True,
            (255, 255, 255),
        )

        artist_surface = self.artist_font.render(
            artist,
            True,
            (175, 175, 175),
        )

        status = (
            "Playing"
            if state.spotify_playing
            else "Paused"
        )

        if state.spotify_device_name:
            status += (
                " • "
                + state.spotify_device_name
            )

        status_surface = self.small_font.render(
            status,
            True,
            (125, 125, 125),
        )

        surface.blit(
            title_surface,
            title_surface.get_rect(
                center=(200, 289)
            ),
        )

        surface.blit(
            artist_surface,
            artist_surface.get_rect(
                center=(200, 320)
            ),
        )

        surface.blit(
            status_surface,
            status_surface.get_rect(
                center=(200, 348)
            ),
        )

        if state.spotify_error:
            error = self.shorten(
                self.small_font,
                state.spotify_error,
                345,
            )

            error_surface = self.small_font.render(
                error,
                True,
                (220, 120, 120),
            )

            surface.blit(
                error_surface,
                error_surface.get_rect(
                    center=(200, 375)
                ),
            )
