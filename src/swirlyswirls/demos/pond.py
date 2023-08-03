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


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Pond Demo'
        self.cache = {}
        self.group = sw.ReversedGroup()
        self.momentum = False

        self.label = self.persist.font.render('Press space to toggle momentum', True, 'white')

        self.ecs_register_systems()

        self.launch_emitter(self.app.rect.center,
                            sw.Emitter(
                                ept0=3, ept1=3, tick=0.05,
                                zone=swirlyswirls.zones.ZoneCircle(r0=0, r1=128),
                                particle_factory=partial(self.pond_particle_factory,
                                                 group=self.group, cache=self.cache),
                                inherit_momentum=3),
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
                    ecs.add_system(ecsc.momentum_system, 'momentum', 'position')
                else:
                    ecs.remove_system(ecsc.momentum_system)

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
        ecs.add_system(sw.emitter_system, 'emitter', 'position', 'lifetime')
        ecs.add_system(sw.particle_system, 'particle', 'lifetime')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    @staticmethod
    def launch_emitter(position, emitter):
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'lifetime', Cooldown(5).pause())

    @staticmethod
    def pond_particle_factory(t, position, momentum, group, cache):
        e = ecs.create_entity()
        image_factory = partial(
            swirlyswirls.particles.bubble_image_factory,
            base_color='aqua', highlight_color='white')

        p = sw.Particle(size_min=5, size_max=10,
                        # alpha_min=0, alpha_max=255,
                        alpha_min=255, alpha_max=0,
                        image_factory=image_factory)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(p, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'lifetime', Cooldown(1))
        ecs.add_component(e, 'cache', cache)
