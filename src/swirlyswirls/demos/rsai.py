import pygame
import tinyecs as ecs
import tinyecs.compsys as ecsc
import swirlyswirls as sw
import swirlyswirls.compsys as swcs
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial, cache

from pgcooldown import Cooldown, LerpThing
from pygame import Vector2
from pygamehelpers.utils import lerp
from pygamehelpers.framework import GameState
from pygamehelpers.easing import *  # noqa


def _image_factory(size, rotate=0, scale=1, alpha=255):
    scaled = size * scale
    r = scaled / 2
    rect = pygame.FRect(0, 0, scaled, scaled)

    image = pygame.Surface((scaled, scaled), pygame.SRCALPHA)
    # pygame.draw.circle(image, 'white', (r, r), r, width=1)
    pygame.draw.rect(image, 'white', rect, width=1)
    pygame.draw.line(image, 'red', (0, r), (r, r), width=1)

    if rotate:
        image = pygame.transform.rotate(image, rotate)
    if alpha != 255:
        image.set_alpha(alpha)

    return image


def _particle_entity_factory(t, position, momentum,
                             image_factory, sprite_group):
    rsai = ecsc.RSAImage(None, image_factory=image_factory)
    # rsai = ecsc.RSAImage(Demo._image_factory(32))
    sprite = ecsc.EVSprite(rsai, sprite_group)
    particle = sw.Particle(
        rotate=LerpThing(vt0=0, vt1=360, repeat=1, interval=1.3, ease=in_quint),  # noqa: F405
        scale=LerpThing(vt0=1, vt1=3, repeat=2, interval=1, ease=out_bounce),  # noqa: F405
        alpha=LerpThing(vt0=255, vt1=64, repeat=2, interval=0.5))

    e = ecs.create_entity()
    ecs.add_component(e, 'particle', particle)
    ecs.add_component(e, 'sprite', sprite)
    ecs.add_component(e, 'rsai', rsai)
    ecs.add_component(e, 'position', Vector2(position))
    ecs.add_component(e, 'momentum', Vector2(momentum) * 1)
    ecs.add_component(e, 'world', pygame.display.get_surface().get_rect())
    ecs.add_component(e, 'lifetime', Cooldown(10))


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'RSAI/LerpThing Demo'
        self.group = pygame.sprite.Group()
        self.emitter_factory()
        self.momentum = True

    def emitter_factory(self):

        # image_factory = partial(image_factory_wrapper, size=32)
        image_factory = partial(_image_factory, size=8)

        particle_entity_factory = partial(
            _particle_entity_factory,
            image_factory=image_factory,
            sprite_group=self.group)

        zone = swirlyswirls.zones.ZoneCircle(r0=0, r1=128)

        emitter = sw.Emitter(ept0=1, ept1=1, tick=0.1, zone=zone,
                             particle_factory=particle_entity_factory,
                             inherit_momentum=3)

        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', Vector2(self.app.rect.center))
        ecs.add_component(e, 'lifetime', Cooldown(9999))

    def reset(self, persist=None):
        """Reset settings when re-running."""
        super().reset(persist=persist)
        ...

    def dispatch_event(self, e):
        """Handle user events"""
        super().dispatch_event(e)

        match e.type:
            case pygame.KEYDOWN if e.key == pygame.K_SPACE:
                self.momentum = not self.momentum
                print('toggle')
                if self.momentum:
                    ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
                else:
                    ecs.remove_system(ecsc.momentum_system)
            case pygame.KEYDOWN if e.key == pygame.K_RETURN:
                self.emitter_factory()

    def update(self, dt):
        """Update frame by delta time dt."""

        ecs.run_system(dt, swcs.container_system, 'world', 'position', 'momentum', 'sprite')
        if self.momentum:
            ecs.run_system(dt, ecsc.momentum_system, 'momentum', 'position')
        ecs.run_system(dt, sw.emitter_system, 'emitter', 'position')
        ecs.run_system(dt, swcs.particle_rsai_system, 'particle', 'rsai')
        ecs.run_system(dt, ecsc.sprite_system, 'sprite', 'position')

        self.group.update(dt)

        sprites = len(self.group.sprites())
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')

        self.group.draw(screen)

        pygame.display.flip()
