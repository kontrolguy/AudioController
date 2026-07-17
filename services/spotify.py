from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path

import requests
import spotipy
from dotenv import load_dotenv
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth


PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "cache"
TOKEN_CACHE_PATH = PROJECT_DIR / ".spotify_cache"
API_REFRESH_SECONDS = 0.5

SCOPES = " ".join(
    [
        "user-read-playback-state",
        "user-read-currently-playing",
        "user-modify-playback-state",
    ]
)

load_dotenv(PROJECT_DIR / ".env")


@dataclass(frozen=True)
class PlaybackState:
    connected: bool = False
    playing: bool = False
    title: str = ""
    artist: str = ""
    album: str = ""
    track_id: str = ""
    artwork_path: str = ""
    position_ms: int = 0
    duration_ms: int = 0
    position_timestamp: float = 0.0
    volume_percent: int = 0
    device_id: str = ""
    device_name: str = ""
    error: str = ""


class LibrespotProcess:
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None

        executable = shutil.which("librespot")

        if executable is None:
            cargo_path = (
                Path.home()
                / ".cargo"
                / "bin"
                / "librespot.exe"
            )

            if cargo_path.exists():
                executable = str(cargo_path)

        if executable is None:
            raise FileNotFoundError(
                "librespot executable not found"
            )

        self.executable = executable

    def start(self) -> None:
        if (
            self.process is not None
            and self.process.poll() is None
        ):
            return

        cache_directory = PROJECT_DIR / "librespot_cache"
        cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        device_name = os.getenv(
            "SPOTIFY_DEVICE_NAME",
            "AudioController Test",
        ).strip()

        command = [
            self.executable,
            "--name",
            device_name,
            "--bitrate",
            "320",
            "--cache",
            str(cache_directory),
            "--initial-volume",
            "50",
            "--device-type",
            "speaker",
        ]

        self.process = subprocess.Popen(
            command,
            cwd=PROJECT_DIR,
        )

    def stop(self) -> None:
        if self.process is None:
            return

        if self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        self.process = None


class SpotifyService:
    def __init__(self) -> None:
        client_id = os.getenv(
            "SPOTIPY_CLIENT_ID",
            "",
        ).strip()

        client_secret = os.getenv(
            "SPOTIPY_CLIENT_SECRET",
            "",
        ).strip()

        redirect_uri = os.getenv(
            "SPOTIPY_REDIRECT_URI",
            "http://127.0.0.1:8888/callback",
        ).strip()

        if not client_id or not client_secret:
            raise RuntimeError(
                "Spotify credentials missing from .env"
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
        self._last_track_id = ""

        CACHE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        self._stop_event.clear()

        self._worker = threading.Thread(
            target=self._worker_loop,
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

    def _set_state(self, new_state: PlaybackState) -> None:
        with self._lock:
            self._state = new_state

    def request_refresh(self) -> None:
        self._refresh_event.set()

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            self._refresh()
            self._refresh_event.wait(
                API_REFRESH_SECONDS
            )
            self._refresh_event.clear()

    def _refresh(self) -> None:
        try:
            playback = self.client.current_playback()

            if not playback:
                self._last_track_id = ""
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
                old = self.get_state()
                self._set_state(
                    replace(
                        old,
                        connected=True,
                        playing=bool(
                            playback.get("is_playing")
                        ),
                        device_id=str(
                            device.get("id") or ""
                        ),
                        device_name=str(
                            device.get("name") or ""
                        ),
                        volume_percent=int(
                            device.get(
                                "volume_percent"
                            ) or 0
                        ),
                        error="No track metadata",
                    )
                )
                return

            artists = ", ".join(
                artist.get("name", "")
                for artist in item.get(
                    "artists",
                    [],
                )
                if artist.get("name")
            )

            album = item.get("album") or {}
            track_id = str(item.get("id") or "")

            images = album.get("images") or []
            artwork_url = (
                str(images[0].get("url") or "")
                if images
                else ""
            )

            old = self.get_state()
            artwork_path = old.artwork_path

            if track_id != self._last_track_id:
                self._last_track_id = track_id
                artwork_path = self._update_artwork(
                    artwork_url,
                    track_id,
                )

            self._set_state(
                PlaybackState(
                    connected=True,
                    playing=bool(
                        playback.get("is_playing")
                    ),
                    title=str(
                        item.get("name") or ""
                    ),
                    artist=artists,
                    album=str(
                        album.get("name") or ""
                    ),
                    track_id=track_id,
                    artwork_path=artwork_path,
                    position_ms=int(
                        playback.get("progress_ms") or 0
                    ),
                    duration_ms=int(
                        item.get("duration_ms") or 0
                    ),
                    position_timestamp=time.monotonic(),
                    volume_percent=int(
                        device.get(
                            "volume_percent"
                        ) or 0
                    ),
                    device_id=str(
                        device.get("id") or ""
                    ),
                    device_name=str(
                        device.get("name") or ""
                    ),
                    error="",
                )
            )

        except SpotifyException as error:
            old = self.get_state()
            self._set_state(
                replace(
                    old,
                    connected=False,
                    error=(
                        f"Spotify API error "
                        f"{error.http_status}: "
                        f"{error.msg}"
                    ),
                )
            )

        except Exception as error:
            old = self.get_state()
            self._set_state(
                replace(
                    old,
                    connected=False,
                    error=(
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                )
            )

    def _update_artwork(
        self,
        url: str,
        track_id: str,
    ) -> str:
        if not url or not track_id:
            return ""

        artwork_path = (
            CACHE_DIR / f"{track_id}.jpg"
        )

        if artwork_path.exists():
            return str(artwork_path)

        temporary_path = (
            CACHE_DIR / f"{track_id}.tmp"
        )

        try:
            response = requests.get(
                url,
                timeout=8,
                headers={
                    "User-Agent":
                    "AudioController/1.0"
                },
            )
            response.raise_for_status()

            temporary_path.write_bytes(
                response.content
            )
            temporary_path.replace(
                artwork_path
            )

            return str(artwork_path)

        except requests.RequestException as error:
            print(
                f"Artwork download error: {error}"
            )
            return ""

        finally:
            if temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

    def _device_id(self) -> str | None:
        current = self.get_state()

        if current.device_id:
            return current.device_id

        try:
            devices = self.client.devices().get(
                "devices",
                [],
            )

            for device in devices:
                if (
                    device.get("name")
                    == self.preferred_device_name
                ):
                    return device.get("id")

        except SpotifyException:
            pass

        return None

    def play_pause(self) -> None:
        current = self.get_state()
        device_id = self._device_id()

        try:
            if current.playing:
                self.client.pause_playback(
                    device_id=device_id
                )
            else:
                self.client.start_playback(
                    device_id=device_id
                )
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def next_track(self) -> None:
        try:
            self.client.next_track(
                device_id=self._device_id()
            )
        except SpotifyException as error:
            self._set_command_error(error)

        self.request_refresh()

    def previous_track(self) -> None:
        try:
            self.client.previous_track(
                device_id=self._device_id()
            )
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

    def _set_command_error(
        self,
        error: SpotifyException,
    ) -> None:
        old = self.get_state()
        self._set_state(
            replace(
                old,
                error=(
                    f"Spotify API error "
                    f"{error.http_status}: "
                    f"{error.msg}"
                ),
            )
        )
