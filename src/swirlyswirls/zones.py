from dataclasses import dataclass
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
