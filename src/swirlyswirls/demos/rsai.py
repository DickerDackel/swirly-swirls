import pygame
import tinyecs as ecs
import tinyecs.compsys as ecsc
import swirlyswirls as sw
import swirlyswirls.compsys as swcs
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial
from random import random

from pgcooldown import Cooldown, LerpThing
from pygame import Vector2
from pygamehelpers.framework import GameState
from rpeasings import *  # noqa


def update_zone_system(dt, eid, zone, momentum):
    phi = momentum.as_polar()[1] + 180
    zone.phi0 = phi - 15
    zone.phi1 = phi + 15


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
        rotate=LerpThing(0, 360, 1.3, repeat=1, ease=in_quint),  # noqa: F405
        scale=LerpThing(1, 3, 1, repeat=2, ease=out_bounce),  # noqa: F405
        alpha=LerpThing(255, 0, 10, repeat=0))

    e = ecs.create_entity()
    ecs.add_component(e, 'particle', particle)
    ecs.add_component(e, 'sprite', sprite)
    ecs.add_component(e, 'rsai', rsai)
    ecs.add_component(e, 'position', Vector2(position))
    ecs.add_component(e, 'momentum', Vector2(momentum) * 2)
    ecs.add_component(e, 'world', pygame.display.get_surface().get_rect())
    ecs.add_component(e, 'lifetime', Cooldown(10))
    ecs.add_component(e, 'kill-target', True)
    return e


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'RSAI/LerpThing Demo'
        self.group = pygame.sprite.Group()
        self.emitter_factory()
        self.emitting = False
        self.label = self.persist.font.render('Press space to toggle emitter', True, 'white')

        _particle_entity_factory(0, position=Vector2(self.app.rect.center),
                                 momentum=Vector2(),
                                 image_factory=partial(_image_factory, size=64),
                                 sprite_group=self.group)

    def emitter_factory(self):

        position = Vector2(self.app.rect.center)
        # momentum = Vector2(50, 0).rotate(random() * 360)
        momentum = Vector2(37, 42)

        # image_factory = partial(image_factory_wrapper, size=32)
        image_factory = partial(_image_factory, size=8)

        particle_entity_factory = partial(
            _particle_entity_factory,
            image_factory=image_factory,
            sprite_group=self.group)

        zone = swirlyswirls.zones.ZoneCircle(r0=0, r1=128)

        emitter = sw.Emitter(ept=LerpThing(5, 5, 0), tick=0.05, zone=zone,
                             particle_factory=particle_entity_factory,
                             inherit_momentum=2)

        sprite = ecsc.ESprite(self.group)
        sprite.image = pygame.Surface((8, 8))
        sprite.rect = sprite.image.get_rect()
        pygame.draw.circle(sprite.image, 'yellow', (4, 4), 4)

        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', position)
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'sprite', sprite)
        ecs.add_component(e, 'world', self.app.rect)
        ecs.add_component(e, 'zone', zone)

    def reset(self, persist=None):
        """Reset settings when re-running."""
        super().reset(persist=persist)
        ...

    def dispatch_event(self, e):
        """Handle user events"""
        super().dispatch_event(e)

        match e.type:
            case pygame.KEYDOWN:
                match e.key:
                    case pygame.K_SPACE:
                        self.emitting = not self.emitting
                    case pygame.K_k:
                        def killall_system(dt, eid, sprite):
                            ecs.remove_entity(eid)
                        ecs.run_system(0, killall_system, 'kill-target')

    def update(self, dt):
        """Update frame by delta time dt."""

        ecs.run_system(dt, swcs.container_system, 'world', 'position', 'momentum', 'sprite')
        ecs.run_system(dt, ecsc.momentum_system, 'momentum', 'position')
        if self.emitting and self.app.clock.get_fps() >= 60:
            ecs.run_system(dt, sw.emitter_system, 'emitter', 'position')
        ecs.run_system(dt, swcs.particle_rsai_system, 'particle', 'rsai')
        ecs.run_system(dt, ecsc.sprite_system, 'sprite', 'position')
        ecs.run_system(dt, ecsc.lifetime_system, 'lifetime')
        ecs.run_system(dt, update_zone_system, 'zone', 'momentum')

        self.group.update(dt)

        sprites = len(self.group.sprites())
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')
        screen.blit(self.label, (5, 5))

        self.group.draw(screen)

        pygame.display.flip()
