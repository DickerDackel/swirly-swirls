from dataclasses import dataclass, InitVar
from random import random
from pygame import Vector2


@dataclass(kw_only=True)
class ZoneCircle:
    r0: float = 0
    r1: float = 64
    phi0: float = 0
    phi1: float = 360
    rnd: callable = random

    def emit(self):
        r = (self.r1 - self.r0) * self.rnd() + self.r0
        phi = (self.phi1 - self.phi0) * self.rnd() + self.phi0
        v = Vector2(r, 0).rotate(phi)

        return v, v

@dataclass(kw_only=True)
class ZoneBeam:
    v: InitVar[Vector2 | tuple[float, float]]
    width: InitVar[float] = 32
    rnd: callable = random

    def __post_init__(self, v, width):
        self.v = Vector2(v)
        self.w = Vector2(self.v.y, self.v.x).normalize() * width

    def emit(self):
        v = self.v * random()
        w = self.w * (random() - 0.5)
        return v + w, w
