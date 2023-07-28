import pygame

from dataclasses import dataclass, InitVar
from swirlyswirls.compsys import ESprite, cache_key


@dataclass(kw_only=True)
class Bubble:
    """Data for the `bubble_system`.

    See `bubble_system` for details.

    Note
    ----
    The caching mechanisms in here are intended for use with the `trsa_system`.

    Parameters
    ----------
    r0, r1 : float = 2, 32
        initial and final radius
    r_easing : callable = lambda x: x
        An easing function to put over the interpolation of r0 and r1
    alpha0, alpha1: float = 255, 0
        Initial and final alpha of the image
    alpha_easing : callable = lambda x: x
        An easing function to put over the interpolation of alpha0 and alpha1
    base_color, highlight_color : pygame.color.Color
        Colors of the bubble and its edge
    sprite_group : pygame.sprite.Group
        Sprite group to put the bubble object into
    image_cache : dict
        see `swirlyswirl.compsys.trsa_system` for details.

    """
    r0: float = 2
    r1: float = 32
    r_easing: callable = lambda x: x
    alpha0: float = 255
    alpha1: float = 0
    alpha_easing: callable = lambda x: x
    base_color: str = 'grey70'
    highlight_color: str = 'white'
    image_factory : callable = None

    def __hash__(self):
        return id(self)


def bubble_system(dt, eid, bubble, sprite, trsa, lifetime, cache):
    """Manage a bubble entity.

    A bubble exists over the specified `lifetime`.  After that, the entity is
    removed.

    The lifetime is also used as ramp for the radius and alpha of the bubble
    sprite.

    Both radius and alpha are calculated as followed:

        t is the lifetime mapped onto a 0-1 interval
        x = (x_t1 - x_t0) * easing(t) + x_t0

    Then the bubble image is generated with the current radius.  The alpha
    value is passed over to `trsa`

    See `swirlyswirls.compsys.TRSA` for information about cached images,
    scaling and rotation.

    Parameters
    ----------
    bubble : swirlyswirls.particles.Bubble
        Bubble data for the system

    sprite : swirlyswirl.compsys.ESprite
        The sprite to store the bubble image in.

    trsa : swirlyswirls.compsys.TRSA
        Alpha will be stored here.

    lifetime : Cooldown
        Used for both, the radius and alpha ramp, as well as the actual
        lifetime if used with `tinyecs.components.lifetime_system`

    Returns
    -------
    None

    """
    def draw(surface, r, t, highlight_color, base_color):
        pygame.draw.circle(surface, highlight_color, (r, r), r)
        pygame.draw.circle(surface, base_color, (r + 2, r), r - 2)

    image_factory = bubble.image_factory if bubble.image_factory else draw

    t = lifetime.normalized

    r = int((bubble.r1 - bubble.r0) * bubble.r_easing(t) + bubble.r0)
    alpha = int((bubble.alpha1 - bubble.alpha0) * bubble.alpha_easing(t) + bubble.alpha0)

    tag = f'bubble-{int(r)}'
    key = cache_key(tag, 0, 1, 255)
    if key not in cache:
        image = pygame.Surface((2 * r + 1, 2 * r + 1), flags=pygame.SRCALPHA)

        image_factory(image, r, t, bubble.highlight_color, bubble.base_color)

        cache[key] = image

    trsa.alpha = alpha
    sprite.tag = tag
    sprite.image = cache[key]
    sprite.rect = sprite.image.get_rect(bottomleft=(-1, -1))
