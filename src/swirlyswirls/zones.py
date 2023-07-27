import pygame

from dataclasses import dataclass, InitVar
from random import random
from pygame import Vector2


@dataclass(kw_only=True)
class ZoneCircle:
    r0: float = 0
    r1: float = 64
    phi0: float = 0
    phi1: float = 360
    rnd_p: callable = random
    rnd_m: callable = random

    def emit(self):
        r = (self.r1 - self.r0) * self.rnd_p() + self.r0
        phi = (self.phi1 - self.phi0) * random() + self.phi0
        v = Vector2(r, 0).rotate(phi)

        return v, v


@dataclass(kw_only=True)
class ZoneBeam:
    v: InitVar[Vector2 | tuple[float, float]]
    width: InitVar[float] = 32
    rnd_p: callable = random
    rnd_m: callable = random

    def __post_init__(self, v, width):
        self.v = Vector2(v)
        self.w = Vector2(self.v.y, self.v.x).normalize() * width

    def emit(self):
        v = self.v * self.rnd_p()
        w = self.w * (self.rnd_m() - 0.5)
        return v + w, w


@dataclass(kw_only=True)
class ZoneRect:
    r: pygame.rect.Rect
    rnd_p: callable = random
    rnd_m: callable = random

    def emit(self):
        pos = Vector2(int(self.r.width * (self.rnd_p() - 0.5)),
                      int(self.r.height * (self.rnd_p() - 0.5)))
        momentum = pos - Vector2(self.r.center)
        return pos, momentum


@dataclass(kw_only=True)
class ZoneLine:
    v: InitVar[Vector2 | tuple[float, float]]
    speed: InitVar[Vector2 | tuple[float, float]] = None
    variance: float = 0
    rnd_p: callable = random
    rnd_m: callable = random

    def __post_init__(self, v, speed):
        self.v = Vector2(v)
        self.speed = Vector2(speed) if speed else Vector2()

    def emit(self):
        v = self.v * self.rnd_p()
        momentum = self.speed * (1 + self.rnd_m() * self.variance)
        return v, momentum
