import pygame
import tinyecs as ecs
import tinyecs.components as ecsc
import swirlyswirls as sw
import swirlyswirls.compsys as swcs

from functools import partial

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
        self.momentum = False
        self.cooldown = Cooldown(5, cold=True)

        self.label = self.persist.font.render('Press space to toggle momentum', True, 'white')

        self.ecs_register_systems()

        self.emitters = [
            Emitter(
                ept0=2, ept1=5, tick=0.1,
                zone=ZoneCircle(r0=0, r1=16),
                launcher=partial(self.launch_explosion_particle,
                                 group=self.group, cache=self.cache,
                                 max_size=8)
            ),
            Emitter(
                ept0=2, ept1=5, tick=0.1,
                zone=ZoneCircle(r0=0, r1=32),
                launcher=partial(self.launch_explosion_particle,
                                 group=self.group, cache=self.cache,
                                 max_size=16)
            ),
            Emitter(
                ept0=2, ept1=5, tick=0.1,
                zone=ZoneCircle(r0=0, r1=64),
                launcher=partial(self.launch_explosion_particle,
                                 group=self.group, cache=self.cache,
                                 max_size=32)
            ),
        ]

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

        if self.cooldown.cold:
            self.cooldown.reset()
            step = self.app.rect.width // 6
            for i in range(3):
                x = step + i * 2 * step
                pos = (x, self.app.rect.centery)
                self.launch_emitter(pos, self.emitters[i])

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
        ecs.add_system(swcs.trsa_system, 'trsa', 'sprite', 'cache')
        ecs.add_system(swcs.sprite_system, 'sprite', 'trsa')

    @staticmethod
    def launch_emitter(pos, emitter):
        e = ecs.create_entity()
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'trsa', swcs.TRSA(translate=Vector2(pos)))
        ecs.add_component(e, 'lifetime', Cooldown(1))

    @staticmethod
    def launch_explosion_particle(position, momentum, parent, group, cache, max_size):
        e = ecs.create_entity()
        ecs.add_component(e, 'bubble', Bubble(r0=2, r1=max_size,
                                              alpha0=255, alpha1=0,
                                              r_easing=out_quint, alpha_easing=out_quint,
                                              base_color='orange', highlight_color='yellow',
                                              image_factory=Demo.draw_box_bubble))
        # ecs.add_component(e, 'lifetime', Cooldown(0.75))
        ecs.add_component(e, 'lifetime', Cooldown(2))
        ecs.add_component(e, 'sprite', swcs.ESprite(group))
        ecs.add_component(e, 'trsa', swcs.TRSA(translate=position))
        ecs.add_component(e, 'momentum', momentum * 3)
        ecs.add_component(e, 'cache', cache)
