import pygame
import tinyecs as ecs
import tinyecs.components as ecsc

from functools import partial
from random import random

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState
from pygamehelpers.easing import *  # noqa

from swirlyswirls.spritegroup import ReversedGroup
from swirlyswirls.compsys import (ESprite, TRSA, momentum_system, trsa_system)
from swirlyswirls.particles import Bubble, bubble_system
from swirlyswirls.emitter import Emitter, emitter_system
from swirlyswirls.zones import ZoneLine


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Raindrops Demo'
        self.cache = {}
        self.group = ReversedGroup()
        self.momentum = False

        self.ecs_register_systems()

        self.launch_emitter((-100, -50),
                            Emitter(
                                ept0=30, ept1=30, tick=0.1,
                                zone=ZoneLine(v=(self.app.rect.width + 200, 0),
                                              speed=(100, 700)),
                                launcher=partial(self.launch_drops_particle,
                                                 group=self.group, cache=self.cache,
                                                 world=self.app.rect.scale_by(1.5)))
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
        c = len(list(self.cache.keys()))
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}  {c=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')

        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(emitter_system, 'emitter', 'trsa', 'lifetime')
        ecs.add_system(bubble_system, 'bubble', 'sprite', 'trsa', 'lifetime', 'cache')
        ecs.add_system(momentum_system, 'momentum', 'trsa')
        ecs.add_system(trsa_system, 'trsa', 'sprite', 'cache')

    @staticmethod
    def launch_emitter(pos, emitter):
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'trsa', TRSA(translate=Vector2(pos)))
        ecs.add_component(e, 'lifetime', Cooldown(5).pause())

    @staticmethod
    def launch_drops_particle(position, momentum, parent, group, cache, world):
        e = ecs.create_entity()
        ecs.add_component(e, 'bubble', Bubble(r0=5, r1=5,
                                              alpha0=128, alpha1=128,
                                              base_color='aqua', highlight_color='white'))
        ecs.add_component(e, 'sprite', ESprite(group))
        ecs.add_component(e, 'trsa', TRSA(translate=position))
        ecs.add_component(e, 'momentum', momentum * (random() + 0.5))
        ecs.add_component(e, 'lifetime', Cooldown(10))
        ecs.add_component(e, 'cache', cache)
        ecs.add_component(e, 'deadzone', world)
