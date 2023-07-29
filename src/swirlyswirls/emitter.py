import tinyecs as ecs
import swirlyswirls.zones

from dataclasses import dataclass, InitVar, field
from cooldown import Cooldown
from pygame import Vector2

# See Freya Holmer "The simple yet powerful math we don't talk about":
#     https://www.youtube.com/watch?v=R6UB7mVO3fY
_lerp     = lambda a, b, t: (1 - t) * a + b * t
_inv_lerp = lambda a, b, v: (v - a) / (b - a)
_remap    = lambda a0, a1, b0, b1, v: _lerp(b0, b1, _inv_lerp(a0, a1, v))


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

    tick : float = 0.1
        The heartbeat of the emitter.

    total_emits: int = None
        if set, limit the total number of emits.  Set `exhausted` (see below)
        when reached.

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
            0: emitter + zone (default)
            1: emitter only
            2: zone only


    """
    ept0: int = 1
    ept1: int = 1
    tick: InitVar[float] = 0.1
    total_emits: InitVar[int] = None
    exhausted: bool = field(init=False, default=None)
    zone: swirlyswirls.zones.Zone
    particle_factory: callable
    inherit_momentum: int = 0

    def __post_init__(self, tick, total_emits):
        self.tick = Cooldown(tick, cold=True)
        self.remaining = total_emits if total_emits is not None else -1


def emitter_system(dt, eid, emitter, trsa, lifetime):
    """The management system for Emitter entities.

    The emitter system isn't much more than a heartbeat.

    On each `tick`, between `ept0` (entities per tick) and `ept1` entities are
    launched.

    For every entity, the `emiter.zone` function is called without parameters.
    It is expected to return 1. a `position` Vector2, 2. a `momentum` Vector2.
    The `position` vector is expected to be relative to the `zone` anchor, so
    the `position` of the emitter needs to be added to it.

    Both, `position` and `momentum` are passed into the `emitter.emit`
    function, which is then expectedo to create a particle entity with all
    necessary components.

    The `lifetime` has 2 functions.  1. is the actual lifetime of the emitter
    object, 2. is the time interval to map `ept0` and `ept1` to.  At the
    beginning of the emitter (t0), `ept0` entities per `tick` will be launched.
    At the end of lifetime (t1), `ept1` entities.  During the time inbetween,
    the number is interpolated from the remaining lifetime.


    Parameters
    ----------
    emitter : swirlyswirl.emitter.Emitter
        Management data for the `emitter_system`.
    trsa : swirlyswirl.compsys.TRSA
        `trsa.translate` points to the location of the emitter.
    lifetime : Cooldown = 1
        The lifetime of the emitter.  Also used to calculate the number of
        emits per tick.  See above.

    Returns
    -------
    None

    """
    if emitter.tick.hot:
        return

    if emitter.remaining == 0:
        return

    emitter.tick.reset()
    t = lifetime.normalized

    emits = int(_lerp(emitter.ept0, emitter.ept1, t))

    if emitter.remaining > 0:
        emits = min(emits, emitter.remaining)
        emitter.remaining -= emits

    if emitter.inherit_momentum & 1 and ecs.eid_has(eid, 'momentum'):
        e_momentum = ecs.comp_of_eid(eid, 'momentum')
    else:
        e_momentum = Vector2(0, 0)

    for i in range(emits):
        position, z_momentum = emitter.zone.emit()

        momentum = Vector2()
        if emitter.inherit_momentum & 1:
            momentum += e_momentum
        if emitter.inherit_momentum & 2:
            momentum += z_momentum

        emitter.particle_factory(t=t, position=trsa.translate + position, momentum=momentum)
