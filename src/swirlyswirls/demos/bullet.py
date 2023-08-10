import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls as sw
import swirlyswirls.compsys as swcs
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial
from random import triangular

from pgcooldown import Cooldown, LerpThing
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import out_quint


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Bubble Explosions'
        self.group = sw.ReversedGroup()
        self.cooldown = Cooldown(1, cold=True)

        self.ecs_register_systems()

        self.particle_factory = partial(self.bullet_particle_factory,
                                        group=self.group)
        self.zone_factory = partial(swirlyswirls.zones.ZoneCircle, r0=0)
        self.emitter = partial(sw.Emitter, ept=LerpThing(1, 1, 5), inherit_momentum=3)

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
            momentum = Vector2(100, 0)

            step = self.app.rect.height // 5
            for i in range(5):
                y = i * step + 0.5 * step
                dy = 50 * triangular(-0.5, 0.5, mode=0)
                pf = partial(self.particle_factory, max_size=10 * (i + 1))
                zone = self.zone_factory(r1=5 * i)
                self.emitter_factory(position=(50, y + dy),
                                     momentum=momentum,
                                     emitter=self.emitter(zone=zone, particle_factory=pf))

        ecs.run_all_systems(dt)

        self.group.update(dt)

        sprites = len(self.group.sprites())
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')

        def draw_system(dt, eid, position, emitter, screen=screen):
            pygame.draw.circle(screen, 'grey20', position, emitter.zone.r1, width=1)

        ecs.run_system(1, draw_system, 'position', 'emitter', screen=self.app.screen)
        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def box_bubble_factory(surface, r, t, base_color, highlight_color):
        rect = pygame.Rect(0, 0, 2 * r, 2 * r)

        pygame.draw.rect(surface, highlight_color, rect, width=2)
        rect.centerx += 1
        rect.centery -= 1
        pygame.draw.rect(surface, base_color, rect)

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(swcs.emitter_system, 'emitter', 'position')
        ecs.add_system(swcs.particle_rsai_system, 'particle', 'rsai')
        ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    @staticmethod
    def emitter_factory(position, momentum, emitter):
        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(5))

    @staticmethod
    def bullet_particle_factory(*, t, position, momentum, group, max_size):
        e = ecs.create_entity()

        def squabble_wrapper(rotate, scale, alpha):
            size = max_size * scale
            return swirlyswirls.particles.firesquabble_image_factory(size, alpha)

        rsai = ecsc.RSAImage(None, image_factory=squabble_wrapper)

        p = swcs.Particle(scale=LerpThing(1 / 8, 1, 0.75),
                          alpha=LerpThing(255, 0, 0.75))

        ecs.add_component(e, 'rsai', rsai)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'lifetime', Cooldown(1))
        ecs.add_component(e, 'sprite', ecsc.EVSprite(rsai, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum)
