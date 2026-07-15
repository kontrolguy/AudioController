from __future__ import annotations

import math
import os
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pygame
import requests
import spotipy
from dotenv import load_dotenv
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth


WIDTH = 400
HEIGHT = 400
FPS = 60
API_REFRESH_SECONDS = 0.50

PROJECT_DIR = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_DIR / "cache"
ARTWORK_PATH = CACHE_DIR / "current_artwork.jpg"
TOKEN_CACHE_PATH = PROJECT_DIR / ".spotify_cache"

SCOPES = " ".join(
    [
        "user-read-playback-state",
        "user-read-currently-playing",
        "user-modify-playback-state",
    ]
)


@dataclass(frozen=True)
class PlaybackState:
    connected: bool = False
    playing: bool = False
    title: str = ""
    artist: str = ""
    album: str = ""
    track_id: str = ""
    artwork_url: str = ""
    artwork_path: str = ""
    position_ms: int = 0
    duration_ms: int = 0
    position_timestamp: float = 0.0
    volume_percent: int = 0
    device_id: str = ""
    device_name: str = ""
    shuffle: bool = False
    repeat: str = "off"
    error: str = ""

    def current_position_ms(self) -> int:
        position = self.position_ms

        if self.playing and self.position_timestamp > 0:
            elapsed = max(0.0, time.monotonic() - self.position_timestamp)
            position += int(elapsed * 1000)

        if self.duration_ms > 0:
            position = min(position, self.duration_ms)

        return max(0, position)

    def progress(self) -> float:
        if self.duration_ms <= 0:
            return 0.0

        return max(
            0.0,
            min(1.0, self.current_position_ms() / self.duration_ms),
        )


class SpotifyService:
    def __init__(self) -> None:
        load_dotenv(PROJECT_DIR / ".env")

        client_id = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv(
            "SPOTIPY_REDIRECT_URI",
            "http://127.0.0.1:8888/callback",
        ).strip()

        if not client_id or not client_secret:
            raise RuntimeError(
                "Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in .env"
            )

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SCOPES,
            cache_path=str(TOKEN_CACHE_PATH),
            open_browser=True,
        )

        self.client = spotipy.Spotify(
            auth_manager=auth_manager,
            requests_timeout=5,
            retries=2,
            status_retries=2,
            backoff_factor=0.5,
        )

        self.preferred_device_name = os.getenv(
            "SPOTIFY_DEVICE_NAME",
            "AudioController Test",
        ).strip()

        self._state = PlaybackState()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._refresh_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._last_artwork_url = ""

        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        self._worker = threading.Thread(
            target=self._worker_loop,
            name="spotify-api-worker",
            daemon=True,
        )
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._refresh_event.set()

        if self._worker:
            self._worker.join(timeout=2)

    def get_state(self) -> PlaybackState:
        with self._lock:
            return replace(self._state)

    def request_refresh(self) -> None:
        self._refresh_event.set()

    def _set_state(self, state: PlaybackState) -> None:
        with self._lock:
            self._state = state

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            self._refresh()

            self._refresh_event.wait(API_REFRESH_SECONDS)
            self._refresh_event.clear()

    def _refresh(self) -> None:
        try:
            playback = self.client.current_playback()

            if not playback:
                self._set_state(
                    PlaybackState(
                        connected=True,
                        error="No active Spotify playback",
                    )
                )
                return

            item = playback.get("item")
            device = playback.get("device") or {}

            if not item:
                self._set_state(
                    PlaybackState(
                        connected=True,
                        playing=bool(playback.get("is_playing")),
                        device_id=str(device.get("id") or ""),
                        device_name=str(device.get("name") or ""),
                        volume_percent=int(device.get("volume_percent") or 0),
                        error="No track metadata",
                    )
                )
                return

            artists = ", ".join(
                artist.get("name", "")
                for artist in item.get("artists", [])
                if artist.get("name")
            )

            album = item.get("album") or {}
            images = album.get("images") or []
            artwork_url = str(images[0].get("url") or "") if images else ""
            artwork_path = self._update_artwork(artwork_url)

            new_state = PlaybackState(
                connected=True,
                playing=bool(playback.get("is_playing")),
                title=str(item.get("name") or ""),
                artist=artists,
                album=str(album.get("name") or ""),
                track_id=str(item.get("id") or ""),
                artwork_url=artwork_url,
                artwork_path=artwork_path,
                position_ms=int(playback.get("progress_ms") or 0),
                duration_ms=int(item.get("duration_ms") or 0),
                position_timestamp=time.monotonic(),
                volume_percent=int(device.get("volume_percent") or 0),
                device_id=str(device.get("id") or ""),
                device_name=str(device.get("name") or ""),
                shuffle=bool(playback.get("shuffle_state")),
                repeat=str(playback.get("repeat_state") or "off"),
            )

            self._set_state(new_state)

        except SpotifyException as error:
            message = f"Spotify API error {error.http_status}: {error.msg}"
            old = self.get_state()
            self._set_state(replace(old, connected=False, error=message))

        except Exception as error:
            old = self.get_state()
            self._set_state(
                replace(
                    old,
                    connected=False,
                    error=f"{type(error).__name__}: {error}",
                )
            )

    def _update_artwork(self, url: str) -> str:
        if not url:
            return ""

        if url == self._last_artwork_url and ARTWORK_PATH.exists():
            return str(ARTWORK_PATH)

        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()

            temporary = ARTWORK_PATH.with_suffix(".tmp")
            temporary.write_bytes(response.content)
            temporary.replace(ARTWORK_PATH)

            self._last_artwork_url = url
            return str(ARTWORK_PATH)

        except requests.RequestException:
            return str(ARTWORK_PATH) if ARTWORK_PATH.exists() else ""

    def _device_id(self) -> str | None:
        state = self.get_state()

        if state.device_id:
            return state.device_id

        try:
            devices = self.client.devices().get("devices", [])

            for device in devices:
                if device.get("name") == self.preferred_device_name:
                    return device.get("id")

        except SpotifyException:
            return None

        return None

    def play_pause(self) -> None:
        state = self.get_state()
        device_id = self._device_id()

        try:
            if state.playing:
                self.client.pause_playback(device_id=device_id)
            else:
                self.client.start_playback(device_id=device_id)

        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def next_track(self) -> None:
        try:
            self.client.next_track(device_id=self._device_id())
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def previous_track(self) -> None:
        try:
            self.client.previous_track(device_id=self._device_id())
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def set_volume(self, value: int) -> None:
        value = max(0, min(100, int(value)))

        try:
            self.client.volume(
                volume_percent=value,
                device_id=self._device_id(),
            )
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def toggle_shuffle(self) -> None:
        state = self.get_state()

        try:
            self.client.shuffle(
                not state.shuffle,
                device_id=self._device_id(),
            )
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def cycle_repeat(self) -> None:
        state = self.get_state()
        modes = ["off", "context", "track"]

        try:
            next_mode = modes[(modes.index(state.repeat) + 1) % len(modes)]
        except ValueError:
            next_mode = "off"

        try:
            self.client.repeat(
                next_mode,
                device_id=self._device_id(),
            )
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def transfer_to_preferred_device(self) -> None:
        device_id = self._device_id()

        if not device_id:
            old = self.get_state()
            self._set_state(
                replace(
                    old,
                    error=(
                        f"Device '{self.preferred_device_name}' not found. "
                        "Start librespot first."
                    ),
                )
            )
            return

        try:
            self.client.transfer_playback(
                device_id=device_id,
                force_play=True,
            )
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def _set_command_error(self, error: SpotifyException) -> None:
        old = self.get_state()
        self._set_state(
            replace(
                old,
                error=f"Spotify API error {error.http_status}: {error.msg}",
            )
        )


class SpotifyTestApp:
    def __init__(self) -> None:
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Spotify Web API Test")
        self.clock = pygame.time.Clock()
        self.running = True

        self.service = SpotifyService()
        self.service.start()

        self.title_font = pygame.font.SysFont(None, 30)
        self.artist_font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)
        self.icon_font = pygame.font.SysFont(None, 82)
        self.volume_font = pygame.font.SysFont(None, 58)

        self.cached_artwork_path = ""
        self.cached_artwork: pygame.Surface | None = None

        self.volume_overlay_value = 0
        self.volume_overlay_until = 0.0

    @staticmethod
    def shorten(font: pygame.font.Font, text: str, width: int) -> str:
        if font.size(text)[0] <= width:
            return text

        shortened = text

        while shortened and font.size(shortened + "...")[0] > width:
            shortened = shortened[:-1]

        return shortened + "..."

    def load_artwork(self, path: str) -> pygame.Surface | None:
        if not path:
            return None

        if path == self.cached_artwork_path:
            return self.cached_artwork

        image_path = Path(path)

        if not image_path.exists():
            return None

        try:
            image = pygame.image.load(str(image_path)).convert_alpha()
            image = pygame.transform.smoothscale(image, (190, 190))
            self.cached_artwork_path = path
            self.cached_artwork = image
            return image

        except (pygame.error, OSError):
            return None

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                self.running = False

            elif event.key == pygame.K_SPACE:
                self.service.play_pause()

            elif event.key == pygame.K_n:
                self.service.next_track()

            elif event.key == pygame.K_p:
                self.service.previous_track()

            elif event.key == pygame.K_t:
                self.service.transfer_to_preferred_device()

            elif event.key == pygame.K_s:
                self.service.toggle_shuffle()

            elif event.key == pygame.K_r:
                self.service.cycle_repeat()

            elif event.key == pygame.K_RIGHT:
                state = self.service.get_state()
                value = min(100, state.volume_percent + 5)
                self.service.set_volume(value)
                self.show_volume(value)

            elif event.key == pygame.K_LEFT:
                state = self.service.get_state()
                value = max(0, state.volume_percent - 5)
                self.service.set_volume(value)
                self.show_volume(value)

    def show_volume(self, value: int) -> None:
        self.volume_overlay_value = value
        self.volume_overlay_until = time.monotonic() + 2.0

    def draw_progress_ring(self, progress: float) -> None:
        ring = pygame.Rect(28, 28, 344, 344)

        pygame.draw.arc(
            self.screen,
            (45, 45, 45),
            ring,
            0,
            math.tau,
            10,
        )

        if progress > 0:
            start = -math.pi / 2

            pygame.draw.arc(
                self.screen,
                (30, 140, 255),
                ring,
                start,
                start + progress * math.tau,
                10,
            )

    def draw_placeholder(self) -> None:
        pygame.draw.circle(
            self.screen,
            (32, 32, 32),
            (200, 165),
            95,
        )

        icon = self.icon_font.render("♪", True, (115, 115, 115))
        self.screen.blit(icon, icon.get_rect(center=(200, 165)))

    def draw_volume_overlay(self) -> None:
        if time.monotonic() >= self.volume_overlay_until:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.circle(
            self.screen,
            (25, 25, 30),
            (200, 200),
            105,
        )

        pygame.draw.circle(
            self.screen,
            (30, 140, 255),
            (200, 200),
            105,
            9,
        )

        text = self.volume_font.render(
            f"{self.volume_overlay_value}%",
            True,
            (30, 140, 255),
        )
        self.screen.blit(text, text.get_rect(center=(200, 200)))

    def draw(self) -> None:
        self.screen.fill((15, 15, 15))
        state = self.service.get_state()

        self.draw_progress_ring(state.progress())

        artwork = self.load_artwork(state.artwork_path)

        if artwork:
            self.screen.blit(artwork, artwork.get_rect(center=(200, 165)))
        else:
            self.draw_placeholder()

        title = self.shorten(
            self.title_font,
            state.title or "No playback",
            330,
        )
        artist = self.shorten(
            self.artist_font,
            state.artist or "Spotify Connect",
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

        status_parts = [
            "Playing" if state.playing else "Paused",
            f"{state.volume_percent}%",
        ]

        if state.device_name:
            status_parts.append(state.device_name)

        status_surface = self.small_font.render(
            " • ".join(status_parts),
            True,
            (125, 125, 125),
        )

        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(200, 289)),
        )
        self.screen.blit(
            artist_surface,
            artist_surface.get_rect(center=(200, 320)),
        )
        self.screen.blit(
            status_surface,
            status_surface.get_rect(center=(200, 348)),
        )

        if state.error:
            error = self.shorten(self.small_font, state.error, 345)
            error_surface = self.small_font.render(
                error,
                True,
                (220, 120, 120),
            )
            self.screen.blit(
                error_surface,
                error_surface.get_rect(center=(200, 375)),
            )

        self.draw_volume_overlay()
        pygame.display.flip()

    def run(self) -> None:
        try:
            while self.running:
                self.handle_events()
                self.draw()
                self.clock.tick(FPS)

        finally:
            self.service.stop()
            pygame.quit()


if __name__ == "__main__":
    SpotifyTestApp().run()
