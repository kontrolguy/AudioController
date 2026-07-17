from __future__ import annotations

import threading
import time
from typing import Any

import requests


class HomeAssistant:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        self._states: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._refresh_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._entity_ids: list[str] = []
        self._last_error = ""

    def start(self, entity_ids: list[str], refresh_seconds: float = 3.0) -> None:
        self._entity_ids = list(dict.fromkeys(entity_ids))

        if self._worker and self._worker.is_alive():
            return

        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._worker_loop,
            args=(refresh_seconds,),
            name="home-assistant-worker",
            daemon=True,
        )
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._refresh_event.set()

        if self._worker:
            self._worker.join(timeout=2)

        self.session.close()

    def request_refresh(self) -> None:
        self._refresh_event.set()

    def _worker_loop(self, refresh_seconds: float) -> None:
        while not self._stop_event.is_set():
            self.refresh_states()
            self._refresh_event.wait(refresh_seconds)
            self._refresh_event.clear()

    def refresh_states(self) -> None:
        new_states: dict[str, dict[str, Any]] = {}

        try:
            for entity_id in self._entity_ids:
                response = self.session.get(
                    f"{self.url}/api/states/{entity_id}",
                    timeout=2.5,
                )
                response.raise_for_status()
                new_states[entity_id] = response.json()

            with self._lock:
                self._states.update(new_states)
                self._last_error = ""

        except requests.RequestException as error:
            with self._lock:
                self._last_error = str(error)

    def get_cached_state(self, entity_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._states.get(entity_id)
            return dict(state) if state else None

    def get_last_error(self) -> str:
        with self._lock:
            return self._last_error

    def get_state(self, entity_id: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.url}/api/states/{entity_id}",
            timeout=3,
        )
        response.raise_for_status()
        return response.json()

    def toggle(self, entity_id: str) -> None:
        domain = entity_id.split(".", 1)[0]

        response = self.session.post(
            f"{self.url}/api/services/{domain}/toggle",
            json={"entity_id": entity_id},
            timeout=4,
        )
        response.raise_for_status()

        # A service call után rögtön frissítsük a kijelzett állapotot.
        self.request_refresh()
