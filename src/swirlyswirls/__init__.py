"""swirlyswirls - A dynamic system of autonomous particles

FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME
             _____ _____  ____  __ _____
            |  ___|_ _\ \/ /  \/  | ____|
            | |_   | | \  /| |\/| |  _|
            |  _|  | | /  \| |  | | |___
            |_|   |___/_/\_\_|  |_|_____|

FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME

While many implementations define a particle system as a monolith, with the
particle manager being responsible for launch, lifetime and motion, and
termination of particles, this library, together with `tinyecs`, takes a
different approach.

Here, an emitter is not much more than a scheduler to launch new entities.

An Emitter is a component that controls initial position, momentum, creation
frequency and number of particles.

A particle is a fully functional entity, not a thing that is managed by the
particle system.

This library tries to keep this as meta as possible, by plugging in all moving
parts.

The following components are involved:

    1. A particle factory, that will create an entity for the particle.

        This function is responsible to create a full entity.  It is not an
        object that has a defined behaviour.  The emitter provides it with the
        settings it has control over, the rest is left to the user.

        To allow more customization of the particle factory, you can make it a
        `partial` that has preconfigured the information you can provide.
        Then hand that partial over to the emitter who then adds above
        arguments.

        The particle factory will receive the following arguments from the
        emitter:

            t: float
                The emit duration of the emitter, mapped onto a 0-1 range

            position: Vector2
                The position where the particle should be created.

            momentum: Vector2
                The momentum (a.k.a speed) the particle should have.

    2. A zone object, that defines the area where the emitted particle
       appears.  Some presets are available, but writing your own zone is
       easy.

       The only parameter a zone receives is the `t` that is also passed into
       the particle factory above.

    3. The `Emitter` object that controls the creation of particles:

        See `swirlyswirls.Emitter` for Details.

        Over its emit duration, it creates between ept0 (Emits Per Tick) and
        ept1 particles per tick.  Besides the time constraint, also the total
        amount of emits can be limited.

        It receives the zone and particle factory as well as the parameters to
        control the emits over time.

    Example:
    --------

        Start with a particle object that you want to emit:

            ```py
            class MySprite(tinyecs.components.ESprite):
                def __init__(self, *groups):
                    super().__init__(*groups)
                    self.image = pygame.Surface((32, 32))
                    self.rect = self.image.get_rect()
            ```

        Now create the particle factory:

            def particle_factory(t, position, momentum, *groups):
                e = ecs.create_entity()
                ecs.add_component(e, 'sprite', MySprite(*groups))
                ecs.add_component(e, 'position', position)
                if momentum is not None:
                    ecs.add_component(e, 'momentum', momentum)

        That will be sufficient, but it lacks e.g. lifecycle management. To add
        this, write the factory function as it is needed, then wrap it in a
        `partial` and pass this to the emitter.

            def internal_particle_factory(lifetime, position, momentum, *groups):
                e = ecs.create_entity()
                ecs.add_component(e, 'lifetime', Cooldown(lifetime))
                ecs.add_component(e, 'sprite', MySprite(*groups))
                ecs.add_component(e, 'position', position)
                if momentum is not None:
                    ecs.add_component(e, 'momentum', momentum)

            particle_factory = partial(internal_particle_factory, lifetime=10)

        Define the zone the particles will emit from.  This is the "shape" of
        the emitter:

            zone = swirlyswirls.zones.ZoneCircle(r1=64)

        Create the emitter configuration and the entity:

            emitter = swirlyswirls.Emitter(ept0=3, ept1=3, tick=0.1, zone=zone,
                                           particle_factory=particle_factory)

            e = ecs.create_entity()
            e.add_component(e, 'emitter', emitter)
            e.add_component(e, 'position', Vector2(500, 500))
            e.add_component(e, 'lifetime', 10)

        Finally add the systems:

            ecs.add_system(tinyecs.components.lifetime_system, 'lifetime')
            ecs.add_system(swirlyswirls.emitter_system, 'emitter')
            ecs.add_system(tinyecs.components.momentum_system, 'momentum', 'position')
            ecs.add_system(tinyecs.components.sprite_system, 'sprite', 'position')

        Run them in your game loop:

            ecs.run_all_systems(dt)

For more complex examples look at the the demos in `swirlyswirls.demos` and/or
run `swirlyswirl-demo`, and inspect the `swirlyswirls.bubbles` module.

"""
# flake8: noqa
from .compsys import Emitter, Particle, emitter_system, particle_system
from .spritegroup import ReversedGroup
