import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
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


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Raindrops Demo'
        self.group = sw.ReversedGroup()
        self.momentum = False
        self.pause = False

        self.ecs_register_systems()

        zone = swirlyswirls.zones.ZoneLine(
            v=(self.app.rect.width + 200, 0),
            speed=(100, 700))

        emitter = sw.Emitter(ept=LerpThing(30, 30, 0), zone=zone,
                             particle_factory=partial(self.drops_particle_factory,
                                                      group=self.group,
                                                      world=self.app.rect.scale_by(1.5)))

        self.launch_emitter((-100, -50), emitter)

    def reset(self, persist=None):
        """Reset settings when re-running."""
        super().reset(persist=persist)
        ...

    def dispatch_event(self, e):
        """Handle user events"""
        super().dispatch_event(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            self.pause = not self.pause

    def update(self, dt):
        """Update frame by delta time dt."""
        if not self.pause:
            ecs.run_all_systems(dt)

        self.group.update(dt)

        sprites = len(self.group.sprites())
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')

        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(swcs.emitter_system, 'emitter', 'position')
        ecs.add_system(swcs.particle_rsai_system, 'particle', 'rsai')
        ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')
        ecs.add_system(ecsc.deadzone_system, 'deadzone', 'position')

    @staticmethod
    def launch_emitter(position, emitter):
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(5).pause())

    @staticmethod
    def drops_particle_factory(t, position, momentum, group, world):
        e = ecs.create_entity()

        def bubble_wrapper(rotate, scale, alpha):
            size = 6 / scale
            return swirlyswirls.particles.waterbubble_image_factory(size, alpha)

        rsai = ecsc.RSAImage(None, image_factory=bubble_wrapper)

        # p = sw.Particle(size_min=6, size_max=6,
        #                 alpha_min=128, alpha_max=128,
        #                 image_factory=bubble)

        p = swcs.Particle(scale=LerpThing(1, 1, 10),
                          alpha=LerpThing(128, 128, 10))

        ecs.add_component(e, 'rsai', rsai)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(rsai, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum * (random() + 0.5))
        ecs.add_component(e, 'lifetime', Cooldown(10))
        ecs.add_component(e, 'deadzone', world)
