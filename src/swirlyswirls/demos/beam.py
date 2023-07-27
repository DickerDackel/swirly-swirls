
import pygame
import tinyecs as ecs
import tinyecs.components as ecsc

from functools import partial
from random import random

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import in_quad, out_quad

from swirlyswirls.spritegroup import ReversedGroup
from swirlyswirls.compsys import (ESprite, TRSA, momentum_system, trsa_system)
from swirlyswirls.particles import Bubble, bubble_system
from swirlyswirls.emitter import Emitter, emitter_system
from swirlyswirls.zones import ZoneBeam


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Bubble Explosions'
        self.cache = {}
        self.group = ReversedGroup()
        self.cooldown = Cooldown(3, cold=True)

        self.ecs_register_systems()

        self.emitter = partial(Emitter,
                               ept0=100, ept1=10, tick=0.01,
                               zone=ZoneBeam(v=(self.app.rect.width, 100), width=32),
                               launcher=partial(self.launch_beam_particle,
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

        def draw_system(dt, eid, trsa, emitter, screen=screen):
            pygame.draw.line(screen, 'grey20', trsa.translate,
                             Vector2(trsa.translate) + emitter.zone.v,
                             width=5)

        ecs.run_system(1, draw_system, 'trsa', 'emitter', screen=self.app.screen)
        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def draw_box_bubble(surface, r, highlight_color, base_color):
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
        ecs.add_system(momentum_system, 'momentum', 'trsa')
        ecs.add_system(trsa_system, 'trsa', 'sprite', 'cache')

    @staticmethod
    def launch_emitter(pos, emitter):
        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter())
        ecs.add_component(e, 'trsa', TRSA(translate=Vector2(pos)))
        ecs.add_component(e, 'lifetime', Cooldown(0.5))

    @staticmethod
    def launch_beam_particle(position, momentum, parent, group, cache):
        e = ecs.create_entity()
        ecs.add_component(e, 'bubble', Bubble(r0=8, r1=2,
                                              alpha0=255, alpha1=0,
                                              r_easing=in_quad, alpha_easing=out_quad,
                                              base_color='lightblue',
                                              highlight_color='white',
                                              draw_fkt=Demo.draw_box_bubble))
        ecs.add_component(e, 'lifetime', Cooldown(1.5))
        ecs.add_component(e, 'sprite', ESprite(group))
        ecs.add_component(e, 'trsa', TRSA(translate=Vector2(position)))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'cache', cache)
