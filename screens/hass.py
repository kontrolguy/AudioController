from __future__ import annotations

import pygame


class HassScreen:
    def __init__(self) -> None:
        self.title_font = pygame.font.SysFont(None, 30)
        self.item_font = pygame.font.SysFont(None, 25)
        self.small_font = pygame.font.SysFont(None, 19)

    @staticmethod
    def _format_value(item: dict, current: dict | None) -> str:
        if current is None:
            return "betöltés..."

        value = str(current.get("state", "unknown"))
        attributes = current.get("attributes") or {}
        item_type = item.get("type", "")

        if item_type == "sensor":
            unit = str(attributes.get("unit_of_measurement") or "")
            return f"{value} {unit}".strip()

        if item_type == "door":
            return "nyitva" if value == "on" else "zárva" if value == "off" else value

        if item_type in {"light", "switch", "fan"}:
            return "bekapcsolva" if value == "on" else "kikapcsolva" if value == "off" else value

        if item_type == "climate":
            temperature = attributes.get("current_temperature")
            target = attributes.get("temperature")

            if temperature is not None and target is not None:
                return f"{value} · {temperature}°C → {target}°C"

            if temperature is not None:
                return f"{value} · {temperature}°C"

        return value

    def draw(self, surface, items, selected, ha) -> None:
        title = self.title_font.render(
            "HOME ASSISTANT",
            True,
            (255, 255, 255),
        )
        surface.blit(title, title.get_rect(center=(200, 38)))

        if not items:
            empty = self.item_font.render(
                "Nincs beállított eszköz",
                True,
                (180, 180, 180),
            )
            surface.blit(empty, empty.get_rect(center=(200, 200)))
            return

        selected = max(0, min(selected, len(items) - 1))

        # Hat elem fér el egyszerre. A lista együtt gördül a kijelöléssel.
        first = max(0, min(selected - 2, max(0, len(items) - 6)))
        visible = items[first:first + 6]

        for row, item in enumerate(visible):
            index = first + row
            is_selected = index == selected
            current = ha.get_cached_state(item["entity_id"])
            value = self._format_value(item, current)

            if is_selected:
                pygame.draw.rect(
                    surface,
                    (30, 65, 95),
                    pygame.Rect(20, 78 + row * 47, 360, 39),
                    border_radius=9,
                )

            color = (70, 190, 255) if is_selected else (215, 215, 215)
            prefix = "> " if is_selected else "  "
            text = f'{prefix}{item["name"]}: {value}'

            # Egyszerű szélességkorlátozás.
            while text and self.item_font.size(text)[0] > 340:
                text = text[:-1]
            if text != f'{prefix}{item["name"]}: {value}':
                text = text[:-3] + "..." if len(text) > 3 else text

            rendered = self.item_font.render(text, True, color)
            surface.blit(rendered, (30, 86 + row * 47))

        error = ha.get_last_error()
        if error:
            message = "HA nem elérhető"
            rendered_error = self.small_font.render(
                message,
                True,
                (230, 110, 110),
            )
            surface.blit(
                rendered_error,
                rendered_error.get_rect(center=(200, 376)),
            )
