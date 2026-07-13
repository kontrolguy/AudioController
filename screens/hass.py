import pygame


class HassScreen:


    def draw(self,surface,items,selected):


        font=pygame.font.SysFont(
            None,
            32
        )


        title=font.render(
            "HOME ASSISTANT",
            True,
            (255,255,255)
        )

        surface.blit(
            title,
            (70,40)
        )


        for i,item in enumerate(items):

            color=(0,255,120) if i==selected else (200,200,200)


            text=font.render(
                ("> " if i==selected else "  ")+item,
                True,
                color
            )


            surface.blit(
                text,
                (50,100+i*50)
            )