from cooldown import Cooldown
from dataclasses import dataclass, InitVar


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

    zone : callable
        The zone function.  See `emitter_system` for details.

    """
    ept0: int = 1
    ept1: int = 1
    tick: InitVar[float] = 0.1
    zone: callable
    launcher: callable

    def __post_init__(self, tick):
        self.tick = Cooldown(tick)
        self.exhausted = False


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

    emitter.tick.reset()
    t = lifetime.normalized
    ept = int((emitter.ept1 - emitter.ept0) * t + emitter.ept0)

    for i in range(ept):
        position, momentum = emitter.zone.emit()
        emitter.launcher(position=trsa.translate + position,
                         momentum=momentum,
                         parent=eid)
