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
from pygamehelpers.easing import *  # noqa: 405


class Demo(GameState):
    def __init__(self, app, persist, parent=None):
        super().__init__(app, persist, parent=parent)

        self.title = 'Pond Demo'
        self.group = sw.ReversedGroup()
        self.momentum = False

        self.label = self.persist.font.render('Press space to toggle momentum', True, 'white')

        self.ecs_register_systems()

        self.launch_emitter()

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
        pygame.display.set_caption(f'{self.title} - time={pygame.time.get_ticks()/1000:.2f}  fps={self.app.clock.get_fps():.2f}  {sprites=}')

    def draw(self, screen):
        """Draw current frame to surface screen."""

        screen.fill('black')
        screen.blit(self.label, (5, 5))

        self.group.draw(screen)

        pygame.display.flip()

    def ecs_register_systems(self):
        ecs.add_system(ecsc.lifetime_system, 'lifetime')
        ecs.add_system(swcs.emitter_system, 'emitter', 'position')
        ecs.add_system(swcs.particle_rsai_system, 'particle', 'rsai')
        ecs.add_system(ecsc.sprite_system, 'sprite', 'position')

    def launch_emitter(self):
        emitter = sw.Emitter(ept=LerpThing(3, 3, 0),
                             zone=swirlyswirls.zones.ZoneCircle(r0=0, r1=128),
                             particle_factory=partial(self.pond_particle_factory,
                                                      group=self.group),
                             inherit_momentum=3)
        e = ecs.create_entity('emitter')
        ecs.add_component(e, 'emitter', emitter)
        ecs.add_component(e, 'position', Vector2(self.app.rect.center))
        ecs.add_component(e, 'lifetime', Cooldown(1).pause())

    def pond_particle_factory(self, t, position, momentum, group):
        def image_factory(rotate, scale, alpha):
            size = 10 * scale
            return swirlyswirls.particles.waterbubble_image_factory(size, alpha)

        rsai = ecsc.RSAImage(None, image_factory=image_factory)

        p = swcs.Particle(scale=LerpThing(1 / 2, 1, 1),
                          alpha=LerpThing(255, 0, 1, ease=in_quint))  # noqa: 405

        e = ecs.create_entity()
        ecs.add_component(e, 'rsai', rsai)
        ecs.add_component(e, 'particle', p)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(rsai, group))
        ecs.add_component(e, 'position', Vector2(position))
        ecs.add_component(e, 'momentum', momentum)
        ecs.add_component(e, 'lifetime', Cooldown(1))
