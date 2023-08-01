import pygame

from dataclasses import dataclass
from functools import lru_cache

_lerp     = lambda a, b, t: (1 - t) * a + b * t


@lru_cache(maxsize=1024)
def bubble_image_factory(size, alpha, base_color, highlight_color):
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)

    r = size // 2 - 1
    pygame.draw.circle(surface, highlight_color, (r, r), r)
    pygame.draw.circle(surface, base_color, (r + 2, r), r - 2)

    surface.set_alpha(alpha)

    return surface


@lru_cache(maxsize=1024)
def squabble_image_factory(size, alpha, base_color, highlight_color):
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)
    surface.fill(highlight_color)

    r = surface.get_rect().move(-1, 1)
    pygame.draw.rect(surface, base_color, r)

    surface.set_alpha(alpha)

    return surface


@lru_cache(maxsize=1024)
def _default_image_factory(size, alpha):
    surface = pygame.Surface((size, size), flags=pygame.SRCALPHA)
    surface.fill('white')

    surface.set_alpha(alpha)

    return surface


@dataclass(kw_only=True)
class Particle:
    """Data to manage the lifecycle of a single particle.

    See `particle_system` for details.


    Parameters
    ----------
    size_min, size_max: float = 2, 32
        initial and final surface size

    size_ease: callable = lambda x: x
        An easing function to put over the interpolation of size_min and size_max

    alpha_min, alpha_max: float = 255, 0
        Initial and final alpha of the image

    alpha_ease : callable = lambda x: x
        An easing function to put over the interpolation of alpha_min and alpha_max

    cycle: bool = False
        Should the particle repeat or end its transmogrification

    image_factory : callable = swirlyswirls.particles._bubble_default_image_factory
        A default drawing function for the Bubble component

    Attributes
    ----------
    All parameters are also accessible as attributes.

    size: float
        The lerped size between size_min and size_max for the time t.  Used by the
        `bubble_system`.

    alpha: float
        The lerped alpha between alpha_min and alpha_max for the time t.  Used by the
        `bubble_system`.

    """
    size_min: float = 2
    size_max: float = 32
    size_ease: callable = lambda x: x
    alpha_min: float = 255
    alpha_max: float = 255
    alpha_ease: callable = lambda x: x
    cycle: bool = False
    image_factory : callable = _default_image_factory

    def __post_init__(self):
        self.alpha = self.alpha_min
        self.size = self.size_min

    @property
    def image(self):
        return self.image_factory(size=self.size, alpha=self.alpha)


def particle_system(dt, eid, particle, lifetime):
    """Progress size and alpha over lifetime.

    The `Particle` class configures the dynamicall generation of an `image`
    property to use as a particle with changing size.  The particle_system is
    the functional part for that component.

    Parameters
    ----------
    particle: swirlyswirls.particles.Particle
        Particle data for the system.

    lifetime : Cooldown
        Used for both, the size and alpha ramp.

        The removal of the entity at the end of `lifetime` should be handled by
        tinyecs.components.lifetime_system.  It's not the scope of this system.

    Returns
    -------
    None

    """
    if lifetime.cold and particle.cycle:
        lifetime.reset()

    t = lifetime.normalized

    particle.size = _lerp(particle.size_min, particle.size_max, particle.size_ease(t))
    particle.alpha = _lerp(particle.alpha_min, particle.alpha_max, particle.alpha_ease(t))
