from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
STATUS_FILE = PROJECT_DIR / "spotify_status.json"
CACHE_DIR = PROJECT_DIR / "cache"
ARTWORK_FILE = CACHE_DIR / "album_art.jpg"


def read_status() -> dict[str, Any]:
    try:
        data = json.loads(
            STATUS_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            return data

    except (OSError, json.JSONDecodeError):
        pass

    return {
        "playing": False,
        "title": "",
        "artist": "",
        "album": "",
        "position_ms": 0,
        "duration_ms": 0,
        "artwork_path": "",
        "artwork_url": "",
        "updated_at": time.time(),
    }


def write_status(status: dict[str, Any]) -> None:
    temporary_file = STATUS_FILE.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(
            status,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary_file.replace(STATUS_FILE)


def get_integer(name: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(name, str(default)))

    except (TypeError, ValueError):
        return default


def get_boolean(name: str) -> bool:
    return os.environ.get(
        name,
        "false",
    ).lower() == "true"


def get_first_line(name: str) -> str:
    value = os.environ.get(name, "")

    for line in value.splitlines():
        line = line.strip()

        if line:
            return line

    return ""


def get_joined_lines(name: str) -> str:
    values = [
        line.strip()
        for line in os.environ.get(name, "").splitlines()
        if line.strip()
    ]

    return ", ".join(values)


def download_artwork(url: str) -> str:
    if not url:
        return ""

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AudioController/1.0",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            artwork_data = response.read()

        temporary_file = ARTWORK_FILE.with_suffix(".tmp")
        temporary_file.write_bytes(artwork_data)
        temporary_file.replace(ARTWORK_FILE)

        return str(ARTWORK_FILE)

    except Exception as error:
        print(f"Artwork download failed: {error}")
        return ""


def main() -> None:
    event = os.environ.get(
        "PLAYER_EVENT",
        "unknown",
    )

    status = read_status()
    now = time.time()

    status["event"] = event
    status["updated_at"] = now

    if event == "track_changed":
        artwork_url = get_first_line("COVERS")

        status.update(
            {
                "track_id": os.environ.get("TRACK_ID", ""),
                "uri": os.environ.get("URI", ""),
                "title": os.environ.get("NAME", ""),
                "artist": get_joined_lines("ARTISTS"),
                "album": os.environ.get("ALBUM", ""),
                "duration_ms": get_integer("DURATION_MS"),
                "position_ms": 0,
                "artwork_url": artwork_url,
            }
        )

        artwork_path = download_artwork(
            artwork_url
        )

        if artwork_path:
            status["artwork_path"] = artwork_path

    elif event == "playing":
        status["playing"] = True
        status["position_ms"] = get_integer(
            "POSITION_MS",
            status.get("position_ms", 0),
        )

        status["position_updated_at"] = now

    elif event == "paused":
        status["playing"] = False
        status["position_ms"] = get_integer(
            "POSITION_MS",
            status.get("position_ms", 0),
        )

        status["position_updated_at"] = now

    elif event in {
        "seeked",
        "position_correction",
    }:
        status["position_ms"] = get_integer(
            "POSITION_MS",
            status.get("position_ms", 0),
        )

        status["position_updated_at"] = now

    elif event in {
        "stopped",
        "end_of_track",
        "unavailable",
    }:
        status["playing"] = False

        if event == "end_of_track":
            status["position_ms"] = status.get(
                "duration_ms",
                0,
            )

    elif event == "volume_changed":
        raw_volume = get_integer("VOLUME")

        status["volume_raw"] = raw_volume
        status["volume_percent"] = round(
            raw_volume * 100 / 65535
        )

    elif event == "shuffle_changed":
        status["shuffle"] = get_boolean("SHUFFLE")

    elif event == "repeat_changed":
        status["repeat_context"] = get_boolean(
            "REPEAT"
        )

        status["repeat_track"] = get_boolean(
            "REPEAT_TRACK"
        )

    elif event == "session_connected":
        status["connected"] = True
        status["spotify_user"] = os.environ.get(
            "USER_NAME",
            "",
        )

    elif event == "session_disconnected":
        status["connected"] = False
        status["playing"] = False

    write_status(status)


if __name__ == "__main__":
    main()