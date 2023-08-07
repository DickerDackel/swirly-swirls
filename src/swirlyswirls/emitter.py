"""Create and run an emitter

An Emitter is a component that controls position, creation frequency and number of
particles.

This library tries to keep this as meta as possible, by plugging in all moving
parts.

The following components are involved:

    1. A particle entity, that should consist of
        - The `emitter` object, required
        - A position, required
        - A lifetime, required
        - A momentum, optional
        - ...

    2. The `Emitter` object that controls the creation of particles:

        See `swirlyswirls.Emitter` below.

        Over the lifetime of the emitter, it emits between ept0 (Emits Per
        Tick) and ept1 particles per tick.



        tick:
            The heartbeat of the emitter

        ept0, ept1, ept_ease:
            emits Per Tick at t0 and t1 (lifetime mapped onto 0 .. 1)
            An optional easing curve to be mapped over the lifetime.

        inherit_momentum:
            See below at particle_factory or `swirlyswirls.Emitter`

        zone:
            A function returning coordinates and momentum.
                See `swirlyswirls.zones.Zone`

        particle_factory:
            A function that provides an image attribute/property.

            This function is responsible for the lifetime management of the
            particle.

            The emitter has no control over the created particle.  It's an
            entity on its own.  Thus the particle factory should be a function
            that creates a new entity including all relevant components.

            The emitter provides the `particle_factory` with `t` of the
            emitter, a position and a momentum which can be either the
            momentum of the zone, the momentum of the emitter, or the sum of
            the two.

    3. The particle factory:

        This function is responsible to create a full entity.  It is not an
        object that has a defined behaviour.  The emitter provides it with the
        settings it has control over, the rest is left to the user.

        To allow more customization of the particle factory, you can make it a
        `partial` that has preconfigured the information you can provide.
        Then hand that partial over to the emitter who then adds above
        arguments.

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

import tinyecs as ecs
import tinyecs.compsys as ecsc
import swirlyswirls.zones

from dataclasses import dataclass, InitVar
from cooldown import Cooldown
from pygame import Vector2
from swirlyswirls.particles import default_image_factory

_lerp     = lambda a, b, t: (1 - t) * a + b * t


@dataclass(kw_only=True)
class Emitter:
    """Data for the `emitter_system`.

    See `emitter_system` for usage.

    Attributes
    ----------
    ept0, ept1 : int = 1
        ept stands for Entities Per Tick and specifies how much entities are to
        be launched on each tick.

        See `emitter_system` for details.

    ept_ease: callable = lambda x: x
        An optional easing curve over the number of emits.  E.g. if you want to
        emit a big burst and then quickly tickle down for the remainder of the
        time.

    duration: float | Cooldown = None
        duration of the emits.  Default `None` is unlimited.

        This is distinct from lifetime, since it might be necessary to access
        the emitter after it has finished emitting (e.g. for particles to kill
        their siblings).

    tick : float = 0.1
        The heartbeat of the emitter.

    total_emits: int = None
        if set, limit the total number of emits.  If the emitter is exhausted,
        the entity removes itself.

        Lifetime does still need to be controlled by a `lifetime` component.
        Reaching `total_emits` will not terminate the emitter object itself.

    zone : callable
        The zone function.  See `emitter_system` for details.

    particle_factory: callable
        A callback to create a particle.

        This function is expected to receive the following parameters:

            t: float
                The normalized lifetime of the emitter (e.g. to shrink
                particle size relative to the age of the emitter)
            position: Vector2
                The position where the particle is emitted
            momentum: Vector2
                The momentum of the particle

    inherit_momentum: 0
        Which momentum to inherit:
            0: no momentum
            1: emitter only
            2: zone only
            3: emitter + zone (default)

    """
    ept0: int = 1
    ept1: int = 1
    ept_ease: callable = lambda x: x
    duration: InitVar[float | Cooldown] = None
    tick: InitVar[float] = 0.1
    total_emits: InitVar[int] = None
    zone: swirlyswirls.zones.Zone
    particle_factory: callable
    inherit_momentum: int = 3

    def __post_init__(self, duration, tick, total_emits):
        self.tick = Cooldown(tick, cold=True)
        self.remaining = total_emits if total_emits is not None else -1

        if duration is None or isinstance(duration, Cooldown):
            self.duration = duration
        else:
            self.duration = Cooldown(duration)


def emitter_system(dt, eid, emitter, position):
    """The management system for Emitter entities.

    The emitter system isn't much more than a heartbeat.

    It's center configuration is the emitter object:

    On each `tick`, between `ept0` (entities per tick) and `ept1` entities are
    launched until `total_emits` is reached or `duration` has passed.

    For every entity, the `emiter.zone` function is called without parameters.
    It is expected to return

        1. a `position` Vector2,
        2. a `momentum` Vector2.

    The `position` vector is expected to be relative to the `zone` anchor, so
    the `position` of the emitter needs to be added to it.

    This system doesn't require a momentum, but it checks if one is available.
    The momentum of the particle is constructed from the momentum the zone
    provided, and the momentum of the emitter, depending on
    `emitter.inherit_momentum` (see `swirlyswirls.Emitter`).

    Both, `position` and `momentum` are passed into the `emitter.emit`
    function, which is then expecte to create a particle entity with all
    necessary components.

    If `emitter.duration` (see `swirlyswirls.Emitter`) is non-zero and
    positive, emits are lerped between ept0 and ept1 based on the length of
    the duration.  If it is negative, duration is assumed to be infinite and
    only ept0 is used.

    Parameters
    ----------
    emitter : swirlyswirl.emitter.Emitter
        Management data for the `emitter_system`.
    position: Vector2
        Position of the emitter

    Returns
    -------
    None

    """

    if emitter.tick.hot:
        return

    emitter.tick.reset()

    if emitter.remaining == 0:
        return

    # If we have a valid duration and it's cold, simply return
    # If we have a valid duration that's hot, get t from it
    # If duration is not valid, try to derive it from lifetime
    # Finally, if all fails, default t to 0
    if emitter.duration is not None:
        if emitter.duration.cold:
            return
        else:
            t = emitter.duration.normalized
    else:
        if ecs.eid_has(eid, 'lifetime'):
            t = ecs.comp_of_eid(eid, 'lifetime').normalized
        else:
            t = 0

    emits = int(_lerp(emitter.ept0, emitter.ept1, emitter.ept_ease(t)))

    if emitter.remaining > 0:
        emits = min(emits, emitter.remaining)
        emitter.remaining -= emits

    if emitter.inherit_momentum & 1 and ecs.eid_has(eid, 'momentum'):
        e_momentum = ecs.comp_of_eid(eid, 'momentum')
    else:
        e_momentum = Vector2(0, 0)

    for i in range(emits):
        z_position, z_momentum = emitter.zone.emit(t)

        momentum = Vector2()
        if emitter.inherit_momentum & 1:
            momentum += e_momentum
        if emitter.inherit_momentum & 2:
            momentum += z_momentum

        emitter.particle_factory(t=t, position=position + z_position, momentum=momentum)


@dataclass(kw_only=True)
class Particle:
    """Data to manage the lifecycle of a single particle.

    See `particle_system` for details.


    Parameters
    ----------
    rotate: LerpThing
        Management of rotation

    scale: LerpThing
        Management of scaling

    alpha: LerpThing
        Management of alpha

    """
    rotate: ecsc.LerpThing
    scale: ecsc.LerpThing
    alpha: ecsc.LerpThing


def particle_system(dt, eid, particle):
    """This is a nop, all lerp things handle their updates automagically"""
    pass
