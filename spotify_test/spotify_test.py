import json
import math
import time
from pathlib import Path

import pygame


WIDTH = 400
HEIGHT = 400
STATUS_FILE = Path("spotify_status.json")


class SpotifyTestApp:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Spotify UI Test")

        self.clock = pygame.time.Clock()
        self.running = True

        self.title_font = pygame.font.SysFont(None, 30)
        self.artist_font = pygame.font.SysFont(None, 24)
        self.status_font = pygame.font.SysFont(None, 21)
        self.icon_font = pygame.font.SysFont(None, 85)

        self.last_file_check = 0.0
        self.file_check_interval = 0.25

        self.data = {
            "playing": False,
            "title": "",
            "artist": "",
            "album": "",
            "position_ms": 0,
            "duration_ms": 0,
            "artwork_path": "",
        }

        self.cached_artwork_path = None
        self.cached_artwork = None

    def load_status(self):
        now = time.monotonic()

        if now - self.last_file_check < self.file_check_interval:
            return

        self.last_file_check = now

        if not STATUS_FILE.exists():
            return

        try:
            with STATUS_FILE.open("r", encoding="utf-8") as file:
                loaded = json.load(file)

            if isinstance(loaded, dict):
                self.data.update(loaded)

        except (OSError, json.JSONDecodeError) as error:
            print(f"Could not read spotify_status.json: {error}")

    def get_progress(self):
        try:
            position = float(self.data.get("position_ms", 0))
            duration = float(self.data.get("duration_ms", 0))

            position_updated_at = float(
                self.data.get(
                    "position_updated_at",
                    self.data.get("updated_at", time.time()),
                )
            )

        except (TypeError, ValueError):
            return 0.0

        if duration <= 0:
            return 0.0

        if self.data.get("playing", False):
            elapsed_seconds = max(0.0, time.time() - position_updated_at)
            position += elapsed_seconds * 1000

        position = min(position, duration)

        return max(0.0, min(1.0, position / duration))

    def load_artwork(self):
        path_value = self.data.get("artwork_path", "")

        if not path_value:
            self.cached_artwork_path = None
            self.cached_artwork = None
            return None

        path = Path(path_value)

        if path_value == self.cached_artwork_path:
            return self.cached_artwork

        if not path.exists():
            return None

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            image = pygame.transform.smoothscale(image, (190, 190))

            self.cached_artwork_path = path_value
            self.cached_artwork = image

            return image

        except (pygame.error, OSError) as error:
            print(f"Artwork load error: {error}")
            return None

    @staticmethod
    def shorten_text(font, text, max_width):
        text = str(text)

        if font.size(text)[0] <= max_width:
            return text

        shortened = text

        while shortened and font.size(shortened + "...")[0] > max_width:
            shortened = shortened[:-1]

        return shortened + "..."

    def draw_progress_ring(self, progress):
        ring_rect = pygame.Rect(28, 28, 344, 344)

        pygame.draw.arc(
            self.screen,
            (45, 45, 45),
            ring_rect,
            0,
            math.tau,
            10,
        )

        if progress <= 0:
            return

        start_angle = -math.pi / 2
        end_angle = start_angle + progress * math.tau

        pygame.draw.arc(
            self.screen,
            (30, 140, 255),
            ring_rect,
            start_angle,
            end_angle,
            10,
        )

    def draw_placeholder(self):
        pygame.draw.circle(
            self.screen,
            (32, 32, 32),
            (200, 165),
            95,
        )

        icon = self.icon_font.render(
            "♪",
            True,
            (115, 115, 115),
        )

        self.screen.blit(
            icon,
            icon.get_rect(center=(200, 165)),
        )

    def draw(self):
        self.screen.fill((15, 15, 15))

        progress = self.get_progress()
        self.draw_progress_ring(progress)

        artwork = self.load_artwork()

        if artwork is not None:
            self.screen.blit(
                artwork,
                artwork.get_rect(center=(200, 165)),
            )
        else:
            self.draw_placeholder()

        title = self.data.get("title") or "No playback"
        artist = self.data.get("artist") or "Spotify Connect"

        title = self.shorten_text(
            self.title_font,
            title,
            330,
        )

        artist = self.shorten_text(
            self.artist_font,
            artist,
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

        status_text = (
            "Playing"
            if self.data.get("playing", False)
            else "Paused"
        )

        status_surface = self.status_font.render(
            status_text,
            True,
            (125, 125, 125),
        )

        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(200, 290)),
        )

        self.screen.blit(
            artist_surface,
            artist_surface.get_rect(center=(200, 322)),
        )

        self.screen.blit(
            status_surface,
            status_surface.get_rect(center=(200, 350)),
        )

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def run(self):
        while self.running:
            self.handle_events()
            self.load_status()
            self.draw()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    app = SpotifyTestApp()
    app.run()