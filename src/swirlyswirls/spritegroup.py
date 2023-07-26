import pygame


class ReversedGroup(pygame.sprite.Group):
    """Identical with pygame.sprite.Group, except the order of sprites is reversed.

    Use this, e.g. for the bubble effect, where the oldest sprites should be
    rendered over new ones.
    """
    def sprites(self):
        return list(reversed(self.spritedict))
