from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
EVENT_SCRIPT = PROJECT_DIR / "librespot_event.cmd"
CACHE_DIR = PROJECT_DIR / "librespot_cache"


def find_librespot() -> str:
    executable = shutil.which("librespot")

    if executable:
        return executable

    cargo_binary = (
        Path.home()
        / ".cargo"
        / "bin"
        / "librespot.exe"
    )

    if cargo_binary.exists():
        return str(cargo_binary)

    raise FileNotFoundError(
        "librespot.exe not found. "
        "Run: cargo install librespot --locked"
    )


def main() -> None:
    librespot = find_librespot()

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        librespot,
        "--name",
        "AudioController Test",
        "--bitrate",
        "320",
        "--cache",
        str(CACHE_DIR),
        "--initial-volume",
        "50",
        "--device-type",
        "speaker",
        "--onevent",
        str(EVENT_SCRIPT),
        "--verbose",
    ]

    print("Starting librespot...")
    print()
    print("Event handler:")
    print(EVENT_SCRIPT)
    print()
    print("Open Spotify and select AudioController Test.")
    print("Press Ctrl+C to stop.")
    print()

    try:
        subprocess.run(
            command,
            cwd=PROJECT_DIR,
            check=False,
        )

    except KeyboardInterrupt:
        print("\nStopping librespot.")


if __name__ == "__main__":
    main()