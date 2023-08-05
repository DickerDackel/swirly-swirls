import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls as sw
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial
from random import random

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import *  # noqa


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

        emitter = sw.Emitter(ept0=30, ept1=30, tick=0.1, zone=zone,
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
        ecs.add_system(sw.emitter_system, 'emitter', 'position')
        ecs.add_system(sw.particle_system, 'particle', 'lifetime')
        ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    @staticmethod
    def launch_emitter(position, emitter):
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(5).pause())

    @staticmethod
    def drops_particle_factory(t, position, momentum, group, world):
        e = ecs.create_entity()
        bubble = partial(
            swirlyswirls.particles.bubble_image_factory,
            base_color='lightblue',
            highlight_color='white',
        )

        p = sw.Particle(size_min=6, size_max=6,
                        alpha_min=128, alpha_max=128,
                        image_factory=bubble)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(p, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum * (random() + 0.5))
        ecs.add_component(e, 'lifetime', Cooldown(10))
        ecs.add_component(e, 'deadzone', world)
