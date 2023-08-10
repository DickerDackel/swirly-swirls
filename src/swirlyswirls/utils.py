"""Unsorted helper classes for swirly swirls...

With the particle system itself comes the needs to create full entities and
have pre-filled Particle definitions for various effects.  These are collected
here, but might migrate into more specific packages at any time.

"""
import tinyecs as ecs

from pygame import Vector2
from pgcooldown import Cooldown

__all__ = ['particle_entity_factory', 'emitter_entity_factory']


def emitter_entity_factory(eid=None, *, emitter, position, momentum,
                           lifetime, **kwargs):
    """A macro to create emitter entities with common components.

    Parameters
    ----------
    eid: hashable
        The eid of the particle to setup.  If None, will be created.

    emitter: swirlyswirls.Emitter
        The configuration object for the emitter_system.

    position,
    momentum: Vector2
        Location and directional speed of the emitter.

    lifetime: float | int | pgcooldown.Cooldown
        Lifetime of the emitter.

    *kwargs:
        All additional key/value pairs will be directly added as
        additional components, with key as the CID and value as the
        component itself.

    Returns
    -------
    EID
        By default, tinyecs creates uuid4 keys as EIDs

    """

    if eid is None:
        eid = ecs.create_entity()

    ecs.add_component(eid, 'emitter', emitter)
    ecs.add_component(eid, 'position', Vector2(position))
    ecs.add_component(eid, 'momentum', Vector2(momentum))
    ecs.add_component(eid, 'lifetime', Cooldown(lifetime))
    for cid, comp in kwargs.items():
        ecs.add_component(eid, cid, comp)

    return eid
    ecs.add_component(e, 'lifetime', Cooldown(5))


def particle_entity_factory(eid=None, *, particle, position, momentum,
                            lifetime, sprite, emitter_eid, **kwargs):
    """A macro to create particle entities with common components.

    Parameters
    ----------
    eid: hashable
        The eid of the particle to setup.  If None, will be created.

    particle: swirlyswirls.Particle
        The particle lifecycle description

    lifetime: float | int | pgcooldown.Cooldown
        Lifetime of the particle

    sprite: pygame.sprite.Sprite
        A normal sprite class will do, but making use of
        swirlyswirls.EVSprite to dynamically generate images from an
        externally plugged in function is recommended.

    position,
    momentum: Vector2
        Location and directional speed of the particle

    emitted_by: hashable
        The EID of the emitter that created this particle.

    *kwargs:
        All additional key/value pairs will be directly added as
        additional components, with key as the CID and value as the
        component itself.

    Returns
    -------
    EID
        By default, tinyecs creates uuid4 keys as EIDs

    """

    if eid is None:
        eid = ecs.create_entity()

    ecs.add_component(eid, 'particle', particle)
    ecs.add_component(eid, 'lifetime', Cooldown(lifetime))
    ecs.add_component(eid, 'sprite', sprite)
    ecs.add_component(eid, 'position', Vector2(position))
    ecs.add_component(eid, 'momentum', Vector2(momentum))
    ecs.add_component(eid, 'emitted-by', emitter_eid)
    for cid, comp in kwargs.items():
        ecs.add_component(eid, cid, comp)

    return eid
