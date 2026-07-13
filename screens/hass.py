import pygame


class HassScreen:


    def draw(self, surface, items, selected, ha):

        font = pygame.font.SysFont(
            None,
            28
        )


        title = font.render(
            "HOME ASSISTANT",
            True,
            (255,255,255)
        )

        surface.blit(
            title,
            (80,30)
        )


        for i, item in enumerate(items[:6]):


            # állapot lekérés
            try:
                current = ha.get_state(
                    item["entity_id"]
                )

                value = current["state"]

            except Exception:

                value = "offline"



            color = (
                (0,255,120)
                if i == selected
                else
                (200,200,200)
            )


            prefix = "> " if i == selected else "  "


            text = font.render(
                prefix
                +
                item["name"]
                +
                " : "
                +
                value,

                True,
                color
            )


            surface.blit(
                text,
                (30,90+i*45)
            )