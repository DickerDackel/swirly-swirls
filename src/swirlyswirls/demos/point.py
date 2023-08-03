import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls as sw
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial
from random import triangular

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import *  # noqa


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Bubble Explosions'
        self.cache = {}
        self.group = sw.ReversedGroup()
        self.cooldown = Cooldown(1, cold=True)

        self.ecs_register_systems()

        # self.launch_particle(position=self.app.rect.center,
        #                      momentum=Vector2(-100, -100),
        #                      group=self.group,
        #                      cache=self.cache)
        self.emitter = partial(sw.Emitter,
                               ept0=5, ept1=5, tick=0.1,
                               zone=swirlyswirls.zones.ZonePoint(speed=100, phi0=150, phi1=210),
                               particle_factory=partial(
                                   self.launch_particle,
                                   group=self.group,
                                   cache=self.cache),
                               )

    def reset(self, persist=None):
        """Reset settings when re-running."""
        super().reset(persist=persist)
        ...

    def dispatch_event(self, e):
        """Handle user events"""
        super().dispatch_event(e)

    def update(self, dt):
        """Update frame by delta time dt."""

        if self.cooldown.cold:
            self.cooldown.reset()
            position = Vector2(-50, self.app.rect.centery)
            momentum = Vector2(150, 0)
            self.launch_emitter(position=position, momentum=momentum, emitter=self.emitter)

        ecs.run_all_systems(dt)

        self.group.update(dt)

        sprites = len(self.group.sprites())
        c = len(list(self.cache.keys()))
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}  {c=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')
        self.group.draw(screen)

        def debug(dt, eid, emitter, position):
            screen = pygame.display.get_surface()
            pygame.draw.circle(screen, 'red', position, 3)
        ecs.run_system(0, debug, 'emitter', 'position')

        pygame.display.flip()

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(sw.emitter_system, 'emitter', 'position', 'lifetime')
        ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
        ecs.add_system(sw.particle_system, 'particle', 'lifetime')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    @staticmethod
    def launch_emitter(*, position, momentum, emitter):
        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter())
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(10))

    @staticmethod
    def launch_particle(*, t=None, position, momentum, group, cache):
        bubble = partial(swirlyswirls.particles.bubble_image_factory,
                         base_color='orange', highlight_color='yellow')

        p = sw.Particle(size_min=2, size_max=16, size_ease=out_quint,  # noqa
                        alpha_min=255, alpha_max=0, alpha_ease=out_quint,  # noqa
                        image_factory=bubble)
        # p = sw.Particle(size_min=2, size_max=16, size_ease=in_quint,  # noqa
        #                 alpha_min=255, alpha_max=0, alpha_ease=out_quint,  # noqa
        #                 image_factory=bubble)

        e = ecs.create_entity()
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'lifetime', Cooldown(1))
        ecs.add_component(e, 'bubble', bubble)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(p, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'cache', cache)
