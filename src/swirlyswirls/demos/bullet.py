import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls.compsys as swcs

from functools import partial
from random import triangular

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import out_quint

from swirlyswirls import (ReversedGroup, Bubble, bubble_system, Emitter,
                          emitter_system, ZoneCircle)


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Bubble Explosions'
        self.cache = {}
        self.group = ReversedGroup()
        self.cooldown = Cooldown(0.1, cold=True)

        self.ecs_register_systems()

        self.emitter = partial(Emitter,
                               ept0=5, ept1=5, tick=0.1,
                               zone=ZoneCircle(r0=0, r1=16),
                               launcher=partial(self.launch_bullet_particle,
                                                group=self.group, cache=self.cache,
                                                max_size=8)
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
            momentum = Vector2(750, 0)
            y = self.app.rect.centery + 50 * triangular(-0.5, 0.5, mode=0)
            self.launch_emitter((50, y), momentum, self.emitter)

        ecs.run_all_systems(dt)

        self.group.update(dt)

        sprites = len(self.group.sprites())
        c = len(list(self.cache.keys()))
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}  {c=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')

        def draw_system(dt, eid, trsa, emitter, screen=screen):
            pygame.draw.circle(screen, 'grey20', trsa.translate, emitter.zone.r1, width=1)

        ecs.run_system(1, draw_system, 'trsa', 'emitter', screen=self.app.screen)
        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def draw_box_bubble(surface, r, t, highlight_color, base_color):
        rect = pygame.Rect(0, 0, 2 * r, 2 * r)

        pygame.draw.rect(surface, highlight_color, rect, width=2)
        rect.centerx += 1
        rect.centery -= 1
        pygame.draw.rect(surface, base_color, rect)

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(emitter_system, 'emitter', 'trsa', 'lifetime')
        ecs.add_system(bubble_system, 'bubble', 'sprite', 'trsa', 'lifetime', 'cache')
        ecs.add_system(swcs.momentum_system, 'momentum', 'trsa')
        ecs.add_system(swcs.trsa_system, 'trsa', 'sprite', 'cache')
        ecs.add_system(swcs.sprite_system, 'sprite', 'trsa')

    @staticmethod
    def launch_emitter(pos, momentum, emitter):
        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter())
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'trsa', swcs.TRSA(translate=Vector2(pos)))
        ecs.add_component(e, 'lifetime', Cooldown(5))

    @staticmethod
    def launch_bullet_particle(position, momentum, parent, group, cache, max_size):
        p_momentum = ecs.comp_of_eid(parent, 'momentum')
        e = ecs.create_entity()
        ecs.add_component(e, 'bubble', Bubble(r0=2, r1=max_size,
                                              alpha0=255, alpha1=0,
                                              r_easing=out_quint, alpha_easing=out_quint,
                                              base_color='orange', highlight_color='yellow',
                                              image_factory=Demo.draw_box_bubble))
        ecs.add_component(e, 'lifetime', Cooldown(1))
        ecs.add_component(e, 'sprite', swcs.ESprite(group))
        ecs.add_component(e, 'trsa', swcs.TRSA(translate=Vector2(position)))
        ecs.add_component(e, 'momentum', p_momentum)
        ecs.add_component(e, 'cache', cache)
