import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls as sw
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import in_quad, out_quad


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Bubble Explosions'
        self.cache = {}
        self.group = sw.ReversedGroup()
        self.cooldown = Cooldown(3, cold=True)

        self.ecs_register_systems()

        self.emitter = partial(
            sw.Emitter,
            ept0=100, ept1=10, tick=0.01,
            inherit_momentum=2,
            zone=swirlyswirls.zones.ZoneBeam(v=(self.app.rect.width, 100), width=32),
            particle_factory=partial(self.beam_particle_factory,
                                     group=self.group, cache=self.cache)
        )

    def reset(self, persist=None):
        """Reset settings when re-running."""
        super().reset(persist=persist)
        ...

    def dispatch_event(self, e):
        """Handle user events"""
        super().dispatch_event(e)
        ...

    def update(self, dt):
        """Update frame by delta time dt."""

        if self.cooldown.cold:
            self.cooldown.reset()
            self.launch_emitter((0, 100), self.emitter)

        ecs.run_all_systems(dt)

        self.group.update(dt)

        sprites = len(self.group.sprites())
        c = len(list(self.cache.keys()))
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}  {c=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')

        def draw_system(dt, eid, position, emitter, screen=screen):
            pygame.draw.line(screen, 'grey20', position, position +
                             emitter.zone.v, width=5)

        ecs.run_system(1, draw_system, 'position', 'emitter', screen=self.app.screen)
        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(sw.emitter_system, 'emitter', 'position', 'lifetime')
        ecs.add_system(sw.particle_system, 'particle', 'lifetime')
        ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    @staticmethod
    def launch_emitter(position, emitter):
        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter())
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(0.5))

    @staticmethod
    def beam_particle_factory(t, position, momentum, group, cache):
        e = ecs.create_entity()
        squabble = partial(
            swirlyswirls.particles.squabble_image_factory,
            base_color='lightblue',
            highlight_color='white',
        )
        p = sw.Particle(size_min=16, size_max=2, size_ease=in_quad,
                        alpha_min=255, alpha_max=0, alpha_ease=out_quad,
                        image_factory=squabble)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'lifetime', Cooldown(1))
        ecs.add_component(e, 'sprite', ecsc.EVSprite(p, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'cache', cache)
