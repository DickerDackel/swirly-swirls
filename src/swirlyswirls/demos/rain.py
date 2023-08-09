import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls as sw
import swirlyswirls.compsys as swcs
import swirlyswirls.particles
import swirlyswirls.zones

from functools import partial

from pgcooldown import Cooldown, LerpThing
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import *  # noqa


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Pond Demo'
        self.group = sw.ReversedGroup()
        self.momentum = False

        self.ecs_register_systems()

        r = self.app.rect.copy()
        r.center = (0, 0)
        self.launch_emitter(self.app.rect.center,
                            sw.Emitter(
                                ept0=3, ept1=1, tick=0.5,
                                zone=swirlyswirls.zones.ZoneRect(r=r),
                                particle_factory=partial(self.pond_particle_factory,
                                                         group=self.group))
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
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    @staticmethod
    def launch_emitter(position, emitter):
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(5).pause())

    @staticmethod
    def pond_particle_factory(t, position, momentum, group):
        def image_factory(rotate, scale, alpha):
            size = 128 * scale
            return Demo.draw_splash_bubble(size, alpha,
                                           base_color='aqua',
                                           highlight_color='white')

        rsai = ecsc.RSAImage(None, image_factory=image_factory)

        p = swcs.Particle(scale=LerpThing(vt0=1 / 10, vt1=1, ease=out_cubic, interval=3), # noqa: 405
                          alpha=LerpThing(vt0=128, vt1=0, ease=out_quad, interval=3))  # noqa: 405

        e = ecs.create_entity()
        ecs.add_component(e, 'rsai', rsai)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(rsai, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'lifetime', Cooldown(3))

    @staticmethod
    def draw_splash_bubble(size, alpha, highlight_color, base_color):
        surface = pygame.Surface((size, size))

        r = size // 2
        pygame.draw.circle(surface, highlight_color, (r, r), r)
        pygame.draw.circle(surface, base_color, (r + 2, r), r - 2)

        for i in range(3):
            pygame.draw.circle(surface, highlight_color, (r, r), (i * r / 3), width=2)

        surface.set_alpha(alpha)

        return surface
