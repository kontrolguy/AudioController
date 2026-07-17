import pygame

from core.state import state


def handle(
    events,
    spotify_service=None,
    home_assistant=None,
):
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue

        if event.key == pygame.K_1:
            state.screen = "clock"

        elif event.key == pygame.K_2:
            state.screen = "spotify"

        elif event.key == pygame.K_3:
            state.screen = "hass"

        elif event.key == pygame.K_RIGHT:
            state.volume = min(
                100,
                state.volume + 5,
            )
            state.show_volume()

            if spotify_service is not None:
                spotify_service.set_volume(
                    state.volume
                )

        elif event.key == pygame.K_LEFT:
            state.volume = max(
                0,
                state.volume - 5,
            )
            state.show_volume()

            if spotify_service is not None:
                spotify_service.set_volume(
                    state.volume
                )

        elif (
            state.screen == "spotify"
            and spotify_service is not None
        ):
            if event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                spotify_service.play_pause()

            elif event.key == pygame.K_n:
                spotify_service.next_track()

            elif event.key == pygame.K_p:
                spotify_service.previous_track()

        elif state.screen == "hass":
            if event.key == pygame.K_DOWN:
                state.hass_selected += 1

                if (
                    state.hass_selected
                    >= len(state.hass_items)
                ):
                    state.hass_selected = 0

            elif event.key == pygame.K_UP:
                state.hass_selected -= 1

                if state.hass_selected < 0:
                    state.hass_selected = (
                        len(state.hass_items) - 1
                    )

            elif event.key == pygame.K_RETURN:
                if state.hass_items:
                    item = state.hass_items[
                        state.hass_selected
                    ]

                    print(
                        "Selected:",
                        item["name"],
                    )

                    if (
                        home_assistant is not None
                        and item.get("type")
                        in {
                            "light",
                            "switch",
                            "fan",
                        }
                    ):
                        home_assistant.toggle(
                            item["entity_id"]
                        )
