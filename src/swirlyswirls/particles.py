import pygame

from dataclasses import dataclass
from functools import lru_cache, partial

_lerp     = lambda a, b, t: (1 - t) * a + b * t


@lru_cache(maxsize=1024)
def default_image_factory(size, alpha, width=1, color='white'):
    """An image factory for squares.

    This is mostly a placeholder for particle classes, but it has basic
    customization for prototyping.

    The `particle_system` will only offer size and alpha.  Make a `partial`
    from this, if you need e.g. a different color.

        red_square = partial(default_image_factory, color='red')

    Then pass this to the `Particle` object.

    Parameters
    ----------
    size: int
        Size of the returned surface.

    alpha: int
        Alpha of the returned surface (0 - 255)

    color: pygame.Color = 'white'
        Particle color

    width: int = 1
        See `pygame.draw,rect`, `width=0` gives a filled square.

    Returns
    -------
    None

    """
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)
    surface.fill('white')

    surface.set_alpha(alpha)

    return surface


@lru_cache(maxsize=1024)
def circle_image_factory(size, alpha, color='white', width=1):
    """An image factory for circles.

    This is mostly a placeholder for particle classes, but it has basic
    customization for prototyping.

    The `particle_system` will only offer size and alpha.  Make a `partial`
    from this, if you need e.g. a different color.

        red_square = partial(default_image_factory, color='red')

    Then pass this to the `Particle` object.

    Parameters
    ----------
    size: int
        Size of the returned surface.

    alpha: int
        Alpha of the returned surface (0 - 255)

    color: pygame.Color = 'white'
        Particle color

    width: int = 1
        See `pygame.draw,rect`, `width=0` gives a filled square.

    Returns
    -------
    None

    """
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)

    r = size // 2
    pygame.draw.circle(surface, color, (r, r), r, width=width)

    surface.set_alpha(alpha)

    return surface


disk_image_factory = partial(circle_image_factory, filled=True)


@lru_cache(maxsize=1024)
def bubble_image_factory(size, alpha, base_color='lightblue', highlight_color='lightcyan'):
    """Image factory for bubbles.

    Bubbles are particles with a slightly highlighted edge, that vary in size
    and/or transparency over its lifetime.  This is controled by the
    `Particle` object and the `particle_system`.

    Parameters
    ----------
    size: int
        Size of the returned surface.

    alpha: int
        Alpha of the returned surface (0 - 255)

    base_color: pygame.Color = 'aqua'
    highlight_color: pygame.Color = 'lightblue'
        Base and edge color of the bubble

    Returns
    -------
    None

    """
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)

    r = size // 2 - 1
    hl_offset = r / 20
    pygame.draw.circle(surface, highlight_color, (r, r), r)
    pygame.draw.circle(surface, base_color, (r + hl_offset, r), r - hl_offset)

    surface.set_alpha(alpha)

    return surface


waterbubble_image_factory = partial(bubble_image_factory,
                                   base_color='lightblue',
                                   highlight_color='white')
waterbubble_image_factory.__doc__ = 'See `bubble_image_factory`, lightblue/white.'

firebubble_image_factory = partial(bubble_image_factory,
                                   base_color='orange',
                                   highlight_color='yellow')
firebubble_image_factory.__doc__ = 'See `bubble_image_factory`, orange/yellow.'

poisonbubble_image_factory = partial(bubble_image_factory,
                                     base_color='palegreen3',
                                     highlight_color='palegreen1')
poisonbubble_image_factory.__doc__ = 'See `bubble_image_factory`, palegreen3/palegreen1.'


@lru_cache(maxsize=1024)
def squabble_image_factory(size, alpha, base_color, highlight_color):
    """Image factory for square bubbles.

    Bubbles are particles with a slightly highlighted edge, that vary in size
    and/or transparency over its lifetime.  This is controled by the
    `Particle` object and the `particle_system`.

    Parameters
    ----------
    size: int
        Size of the returned surface.

    alpha: int
        Alpha of the returned surface (0 - 255)

    base_color: pygame.Color = 'aqua'
    highlight_color: pygame.Color = 'lightblue'
        Base and edge color of the bubble

    Returns
    -------
    None

    """
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)
    surface.fill(highlight_color)

    hl_offset = max(1, size / 20)
    r = surface.get_rect().move(hl_offset, -hl_offset)
    pygame.draw.rect(surface, base_color, r)

    surface.set_alpha(alpha)

    return surface


watersquabble_image_factory = partial(squabble_image_factory,
                                     base_color='lightblue',
                                     highlight_color='white')
watersquabble_image_factory.__doc__ = 'See `squabble_image_factory`, lightblue/white.'

firesquabble_image_factory = partial(squabble_image_factory,
                                     base_color='orange',
                                     highlight_color='yellow')
firesquabble_image_factory.__doc__ = 'See `squabble_image_factory`, orange/yellow.'

poisonsquabble_image_factory = partial(squabble_image_factory,
                                       base_color='palegreen3',
                                       highlight_color='palegreen1')
poisonsquabble_image_factory.__doc__ = 'See `squabble_image_factory`, palegreen3/palegreen1.'
