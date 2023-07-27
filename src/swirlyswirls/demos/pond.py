import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls.compsys as swcs

from functools import partial

from cooldown import Cooldown
from pygame import Vector2
from pygamehelpers.framework import GameState

from swirlyswirls import (ReversedGroup, Bubble, bubble_system, Emitter,
                          emitter_system, ZoneCircle)


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Pond Demo'
        self.cache = {}
        self.group = ReversedGroup()
        self.momentum = False

        self.label = self.persist.font.render('Press space to toggle momentum', True, 'white')

        self.ecs_register_systems()

        self.launch_emitter(self.app.rect.center,
                            Emitter(
                                ept0=3, ept1=3, tick=0.05,
                                zone=ZoneCircle(r0=0, r1=128),
                                launcher=partial(self.launch_pond_particle,
                                                 group=self.group, cache=self.cache))
                            )

    def reset(self, persist=None):
        """Reset settings when re-running."""
        super().reset(persist=persist)
        ...

    def dispatch_event(self, e):
        """Handle user events"""
        super().dispatch_event(e)

        match e.type:
            case pygame.KEYDOWN if e.key == pygame.K_SPACE:
                self.momentum = not self.momentum
                if self.momentum:
                    ecs.add_system(swcs.momentum_system, 'momentum', 'trsa')
                else:
                    ecs.remove_system(swcs.momentum_system)

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
        screen.blit(self.label, (5, 5))

        self.group.draw(screen)

        pygame.display.flip()

    @staticmethod
    def ecs_register_systems():
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(emitter_system, 'emitter', 'trsa', 'lifetime')
        ecs.add_system(bubble_system, 'bubble', 'sprite', 'trsa', 'lifetime', 'cache')
        ecs.add_system(swcs.trsa_system, 'trsa', 'sprite', 'cache')

    @staticmethod
    def launch_emitter(pos, emitter):
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'trsa', swcs.TRSA(translate=Vector2(pos)))
        ecs.add_component(e, 'lifetime', Cooldown(5).pause())

    @staticmethod
    def launch_pond_particle(position, momentum, parent, group, cache):
        e = ecs.create_entity()
        ecs.add_component(e, 'bubble', Bubble(r0=5, r1=10,
                                              # alpha0=0, alpha1=255,
                                              alpha0=128, alpha1=0,
                                              base_color='aqua', highlight_color='white'))
        ecs.add_component(e, 'sprite', swcs.ESprite(group))
        ecs.add_component(e, 'trsa', swcs.TRSA(translate=position))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'lifetime', Cooldown(1))
        ecs.add_component(e, 'cache', cache)
