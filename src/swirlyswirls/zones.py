import pygame

from abc import ABC, abstractmethod
from dataclasses import dataclass, InitVar, field
from random import random, triangular
from pygame import Vector2

# See Freya Holmer "The simple yet powerful math we don't talk about":
#     https://www.youtube.com/watch?v=R6UB7mVO3fY
# This is the "official" lerp, but it's about 10% slower than the one with only
# a single multiplication below.
# _lerp     = lambda a, b, t: (1 - t) * a + b * t
_lerp     = lambda a, b, t: t * (b - a) + a
_inv_lerp = lambda a, b, v: (v - a) / (b - a)
_remap    = lambda a0, a1, b0, b1, v: _lerp(b0, b1, _inv_lerp(a0, a1, v))


@dataclass(kw_only=True)
class Zone(ABC):
    """Derive from this to implement your particle zones.

    A zone is a class that has an emit function, which returns a tuple of
    coordinate and momentum.

    Parameters
    ----------
    The base class has no input parameters.  Extend as you please.

    Attributes
    ----------
    The base class has no input attributes.  Extend as you please.

    """
    @abstractmethod
    def emit(self, t=None):
        """Emit a coordinate/momentum tuple

        Parameters
        ----------
        t
            An optional time, e.g. to use in a `lerp`.  If `None` (the
            defeault), the zone is not time dependent.

        Returns
        -------
        position : Vector2
            Coordinates relative to the zone.  Note, that the emitter will add
            its own position on top of this to launch a particle.

        momentum: Vector2
            Use this to derive a speed for an emitted particle from.  E.g. if
            you're emitting from within a circle, the momentum could be the
            vector from the circle's center to the emitted paraticle.

        """
        raise NotImplementedError


@dataclass(kw_only=True)
class ZonePoint(Zone):
    """A single point zone.

    Emits always return Vector2(0, 0).

    momentum returns a vector of random length between 0 and `speed`, in the
    random direction between `phi0` and `phi1`.

    Parameters
    ----------
    speed: Vector2 = Vector2(0, 0)
        An optional momentum to launch with.  This vector is randomly scaled
        between 0 and 1.

    variance : float = 0..1
        The length of the momentum vector will be scaled by a random between
        `1 - variance` and `1 + variance`.

        A variance of 0 gives you an exact speed.
        A variance of 0.5 gives you random speed between `0.5 * speed` and
        `1.5 * speed`.

    phi0, phi1: = 0, 360
        Start and end angle of the momentum.  If you only want to emit from a
        half circle, set these to 0 and 180 or 90 and 270.

    rnd_m:
        Alternative random functions, e.g. if you want a gauss distribution
        instead of a normal random value.

        Note, that this functions are expected to be parameterless.  Provide a
        lambda if you need them to be configurable.

    Attributes
    ----------
    See Parameters


    """
    speed: Vector2 = field(default_factory=lambda: Vector2())
    variance: float = 0
    phi0: float = 0
    phi1: float = 360
    rnd_m: callable = random

    def emit(self, t=None):
        """Emit a single point.

        Since emits are always relative to the emitter's position, this
        function always returns Vector2(0, 0).

        """
        momentum = Vector2(self.speed, 0) * (1 + self.rnd_m() * 2 * self.variance - self.variance)
        momentum.rotate_ip(_lerp(self.phi0, self.phi1, self.rnd_m()))

        return Vector2(0, 0), momentum


@dataclass(kw_only=True)
class ZoneLine:
    """A zone emitting around on a line.

    Parameters
    ----------
    v: Vector2
        A vector representing the line.  This is always rooted at (0, 0).

    speed : Vector2
        A vector for the direction of the momentum

    variance : float = 0..1
        The length of the momentum vector will be scaled by a random between
        `1 - variance` and `1 + variance`.

        A variance of 0 gives you an exact speed.
        A variance of 0.5 gives you random speed between `0.5 * speed` and
        `1.5 * speed`.

    rnd_p, rnd_m:
        Alternative random functions, e.g. if you want a gauss distribution
        instead of a normal random value.

        Note, that this functions are expected to be parameterless.  Provide a
        lambda if you need them to be configurable.

    Attributes
    ----------
    See Parameters.

    """
    v: InitVar[Vector2 | tuple[float, float]]
    speed: InitVar[Vector2 | tuple[float, float]] = None
    variance: float = 0
    rnd_p: callable = random
    rnd_m: callable = random

    def __post_init__(self, v, speed):
        self.v = Vector2(v)
        self.speed = Vector2(speed) if speed else Vector2()

    def emit(self, t=None):
        """Emit a point along the line.

        Parameters
        ----------
        t : any
            t is ignored by this zone.

        Returns
        -------
        position : Vector2
            A random point on the defined line.

        momentum: Vector2
            The perpendicular distance to the vector of the beam.

        """

        v = self.v * self.rnd_p()
        momentum = self.speed * (1 + self.rnd_m() * 2 * self.variance - self.variance)
        return v, momentum


@dataclass(kw_only=True)
class ZoneCircle(Zone):
    """A circular zone.

    Parameters
    ----------
    r0, r1 : float = 0, 64
        minimum and maximum radius of the zone.  If the minimum is different
        from 0, the zone is a ring instead of a circle.

    phi0, phi1: = 0, 360
        Start and end angle of the circular zone.  If you only want to emit
        from a half circle, set these to 0 and 180 or 90 and 270.

    rnd_p, rnd_m:
        Alternative random functions, e.g. if you want a gauss distribution
        instead of a normal random value.

        Note, that this functions are expected to be parameterless.  Provide a
        lambda if you need them to be configurable.


    Attributes
    ----------
    See Parameters.

    """
    r0: float = 0
    r1: float = 64
    phi0: float = 0
    phi1: float = 360
    rnd_p: callable = random
    rnd_m: callable = random

    def emit(self, t=None):
        """Emit a coordinate/momentum tuple

        Parameters
        ----------
        t : any
            t is ignored by this zone.

        Returns
        -------
        position : Vector2
            A random point, relative to the circle's origin, within the radius
            defined by r0 and r1.

        momentum: Vector2
            With this zone, always identical to `position`.

        """
        r = (self.r1 - self.r0) * self.rnd_p() + self.r0
        phi = (self.phi1 - self.phi0) * random() + self.phi0
        v = Vector2(r, 0).rotate(phi)

        return v, v


@dataclass(kw_only=True)
class ZoneRing(Zone):
    """A dynamically changing ring zone.

    This is a ring, where inner and outer radius can change over time. Setting
    the min radius to 0 can also make this a disk that grows or shrinks.

    Parameters
    ----------
    r_min_t0, r_max_t0,
    r_min_t1, r_max_t1: float
        minimum and maximum radius at beginning and end of lifetime

    r_ease: callable = lambda x: x
        Easing function for t of radius

    phi_min_t0, phi_max_t0,
    phi_min_t1, phi_max_t1: float
        Start and end angle of the ring zone.  If you only want to emit
        from a half ring, set these to 0 and 180 or 90 and 270.

    phi_ease: callable = lambda x: x
        Easing function for t of angle

    rnd_p, rnd_m:
        Alternative random functions, e.g. if you want a gauss distribution
        instead of a normal random value.

        Note, that this functions are expected to be parameterless.  Provide a
        lambda if you need them to be configurable.


    Attributes
    ----------
    See Parameters.

    """
    r_min_t0: float
    r_max_t0: float
    r_min_t1: float = None
    r_max_t1: float = None
    r_ease: callable = lambda x: x

    phi_min_t0: float = 0
    phi_max_t0: float = 360
    phi_min_t1: float = 0
    phi_max_t1: float = 360
    r_ease: callable = lambda x: x

    rnd_p: callable = random
    rnd_m: callable = random

    def emit(self, t=None):
        """Emit a coordinate/momentum tuple

        Parameters
        ----------
        t : any
            t is ignored by this zone.

        Returns
        -------
        position : Vector2
            A random point, relative to the circle's origin, within the radius
            defined by r0 and r1.

        momentum: Vector2
            With this zone, always identical to `position`.

        """
        r_min = _lerp(self.r_min_t0, self.r_min_t1, t)
        r_max = _lerp(self.r_max_t0, self.r_max_t1, t)
        r = _lerp(r_min, r_max, self.rnd_p())

        phi_min = _lerp(self.phi_min_t0, self.phi_min_t1, t)
        phi_max = _lerp(self.phi_max_t0, self.phi_max_t1, t)
        phi = _lerp(phi_min, phi_max, self.rnd_p())

        v = Vector2(r, 0).rotate(phi)

        return v, v


@dataclass(kw_only=True)
class ZoneRect:
    """A rectangular zone.

    Use this e.g. to emit particles all over the screen.

    Parameters
    ----------
    r: pygame.rect.Rect
        The rect to emit from

    rnd_p, rnd_m:
        Alternative random functions, e.g. if you want a gauss distribution
        instead of a normal random value.

        Note, that this functions are expected to be parameterless.  Provide a
        lambda if you need them to be configurable.

    Attributes
    ----------
    See Parameters.

    """
    r: pygame.rect.Rect
    rnd_p: callable = random
    rnd_m: callable = random

    def emit(self, t=None):
        """Emit a point within a rectangle.

        Note: returned points are always relative to the center of the
        rectangle, within

            (-width / 2, -height / 2) and (width / 2, height / 2).

        Parameters
        ----------
        t : any
            t is ignored by this zone.

        Returns
        -------
        position : Vector2
            A random point within the defined rectangle.

        momentum: Vector2
            Same as position

        """
        pos = Vector2(int(self.r.width * (self.rnd_p() - 0.5)),
                      int(self.r.height * (self.rnd_p() - 0.5)))
        momentum = pos - Vector2(self.r.center)
        return pos, momentum


@dataclass(kw_only=True)
class ZoneBeam:
    """A zone emitting around a line.

    Parameters
    ----------
    v: Vector2
        A vector representing the line.  This is always rooted at (0, 0).

    width : float
        The distance perpendicular to the line, at which points will be
        returned.


    rnd_p, rnd_m:
        Alternative random functions, e.g. if you want a gauss distribution
        instead of a normal random value.

        Note, that this functions are expected to be parameterless.  Provide a
        lambda if you need them to be configurable.

        You might want to use `random.triangular` for this, to emit more
        particles directly near the line.

    Attributes
    ----------
    See Parameters.

    """
    v: InitVar[Vector2 | tuple[float, float]]
    width: InitVar[float] = 32
    rnd_p: callable = random
    rnd_m: callable = lambda: triangular(0, 1, mode=0.5)

    def __post_init__(self, v, width):
        self.v = Vector2(v)
        self.w = Vector2(-self.v.y, self.v.x).normalize() * width

    def emit(self, t=None):
        """Emit a point along the line within `width` distance.

        Parameters
        ----------
        t : any
            t is ignored by this zone.

        Returns
        -------
        position : Vector2
            A random point within the defined beam.

        momentum: Vector2
            The perpendicular distance to the vector of the beam.

        """
        v = self.v * self.rnd_p()
        w = self.w * 4 * (self.rnd_m() - 0.5) + self.v.normalize() * 100
        return v, w
