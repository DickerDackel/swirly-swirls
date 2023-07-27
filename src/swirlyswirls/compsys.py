import pygame
import tinyecs as ecs

from dataclasses import dataclass, field
from cooldown import Cooldown
from pygame import Vector2


def cache_key(tag, rotate, scale, alpha):
    return f'{tag}-{int(rotate)}-{int(scale)}-{int(alpha)}'


class ESprite(pygame.sprite.Sprite):
    """A sprite class especially for ECS entities.

    If an entity with a sprite component is removed, the sprite also needs to
    be removed from all sprite groups.

    `tinyecs` offers the `shutdown_` method for this.  If this is available,
    ecs.remove_entity will call it when tearing down an entity.

    Parameters
    ----------
    *groups : *pygame.sprite.Group()
        Directly passed into parent class.  See `pygame.sprite.Sprite` for
        details.

    tag : hashable = None
        A tag to identify this sprite.  Can e.g. be used for image caching.

    """
    def __init__(self, *groups, tag=None):
        super().__init__(*groups)
        self.tag = tag

    def shutdown_(self):
        self.kill()


@dataclass(kw_only=True)
class Fade:
    """Runtime data for the `fade_system`.

    Attributes
    ----------
    t0 : float
        Initial alpha value
    t1 : float
        Final alpha value
    duration : Cooldown
        Duration of the alpha blending

    """
    t0: float = 255
    t1: float = 0
    duration: Cooldown


@dataclass(kw_only=True)
class TRSA:
    """Runtime data for the `trsa_system`.

    TRSA is short for Translation, Rotation, Scale and Alpha.  It is primarily
    used for sprite entities.

    Note: When using this data to scale and rotate an image, the float values
    will be converted to int to make image cache hits possible.

    Attributes
    ----------
    translate : pygame.Vector2
        World position of the entity
    rotate : float = 0
        Rotation of the entity
    scale : float = 1
        Scaling of the entity
    alpha : float = 255
        Alpha blending of the entity (see `fade_system`)

    _image_id : int
        The saved `id(image)` to check, if `_base_image` needs to be updated.
        Reason might be, that the image was updated from outside the class or
        the system.

    """
    translate: Vector2 = field(default_factory=Vector2)
    rotate: float = 0
    scale: float = 1
    alpha: float = 255

    _base_image: pygame.surface.Surface = field(init=False, default=None)
    _image_id: int = field(init=False, default=None)


def acceleration_system(dt, eid, acceleration, momentum):
    """Apply acceleration onto a momentum.

    Parameters
    ----------
    acceleration : pygame.Vector2
        every frame, `acceleration * dt` is added to `momentum`
    momentum : pygame.Vector2
        The current momentum of the entity

    Returns
    -------
    None

    """
    momentum += acceleration * dt


def momentum_system(dt, eid, momentum, trsa):
    """Apply a momentum to the current position.

    Parameters
    ----------
    momentum : pygame.Vector2
        The current momentum of the entity
    trsa : swirlyswirl.compsys.TRSA
        Every frame, `momentum * dt` will be added to `trsa.translate`

    Returns
    -------
    None

    """
    trsa.translate += momentum * dt


def angular_momentum_system(dt, eid, angular_momentum, trsa):
    """Apply a angular momentum to the current angle.

    Parameters
    ----------
    angular_momentum : float
        The current angular momentum of the entity
    trsa : swirlyswirl.compsys.TRSA
        Every frame, `angular_momentum * dt` will be added to `trsa.rotate`
        Angles are in degrees, rounded to 360.

    Returns
    -------
    None

    """
    trsa.rotate = (trsa.rotate + angular_momentum * dt) % 360


def trsa_system(dt, eid, trsa, sprite, cache):
    """Manage translation, rotation and scale ofasprite.

    The trsa object consolidates the world position (and alpha blending) of the sprite entity.

    It scales and rotates the sprite's base image according to the `rotate` and
    `scale` properties, and will set `sprite.rect.center` to `trsa.translate`.

    Rotated and scaled images are cached.  See the module description above for
    details.

    Parameters
    ----------
    trsa : swirlyswirl.compsys.TRSA
        The object consolidating all relevant for the sprite.
    sprite : swirlyswirl.compsys.ESprite
        The entity sprite object to apply the transformation to.

    Returns
    -------
    None

    """
    tag = sprite.tag
    key = cache_key(tag, int(trsa.rotate), int(trsa.scale), int(trsa.alpha))

    if key not in cache:
        base_key = cache_key(tag, 0, 1, 255)
        if base_key not in cache:
            cache[base_key] = sprite.image

        if trsa.rotate != 0 or trsa.scale != 1:
            image = pygame.transform.rotozoom(cache[base_key], trsa.rotate, trsa.scale)
        else:
            image = cache[base_key].copy()

        image.set_alpha(trsa.alpha)
        cache[key] = image

    sprite.image = cache[key]
    sprite.rect = sprite.image.get_rect(center=trsa.translate)


def sprite_system(dt, eid, sprite, trsa):
    """Write position data into the sprite rect.

    This function transfers `trsa.translate` into `sprite.rect.center`, thus
    preparing the sprite to be rendered.

    Use this after all systems that might modify `sprite.image` or `trsa` have
    finished.

    Parameters
    ----------
    sprite : swirlyswirls.compsys.ESprite
        The sprite
    trsa : swirlyswirls.compsys.TRSA
        Location and transform information to apply to the sprite.

    """
    sprite.rect.center = trsa.translate


def fade_system(dt, eid, fade, trsa):
    """Apply alpha blending to the trsa.

    Note: This function *does not* apply the blending to the image.  It only
    modifies `trsa.alpha`.  Like e.g. `momentum_system` does to
    `trsa.translate`.

    The actual apply of the alpha blending to the  image will be done by
    `trsa_system`.

    Parameters
    ----------
    fade : swirlyswirl.compsys.Fade
        The ramp definition of the alpha blending.
    trsa : swirlyswirl.compsys.TRSA
        Every frame, `t * dt` will be added to `trsa.translate`

    Returns
    -------
    None

    """
    t = fade.duration.normalized
    trsa.alpha = (fade.t1 - fade.t0) * t + fade.t0


def container_system(dt, eid, container, trsa, momentum, angular_momentum, sprite):
    """A system to make a sprite bonce off the edges of the screen.

    This is not of use for actual programs, but it's a nice example of a custom
    component.  It can still be used in test programs if you need to manage
    your sprites on screen.

    Parameters
    ----------
    container : pygame.rect.Rect
        The bounding box for the sprites
    trsa : swirlyswirls.compsys.TRSA
        World position and state of the sprite.  If a wall is hit, the position
        will be reset to inside the container.
    momentum
        The momentum of the sprite.  On wall hit, it is inversed on the
        collision axis.
    angular_momentun : float
        The angular momentum of the sprite.  Reversed on wall hits.
    sprite : swirlyswirl.compsys.ESprite
        The visualization of the entity, a.k.a. the sprite to bounce around.

    Returns
    -------
    None

    """
    if sprite.rect.left < container.left and momentum.x < 0:
        momentum.x = -momentum.x
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        trsa.translate.x += -2 * sprite.rect.left
    elif sprite.rect.right > container.right and momentum.x > 0:
        momentum.x = -momentum.x
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        trsa.translate.x += 2 * (container.width - sprite.rect.right)

    if sprite.rect.top < container.top and momentum.x < 0:
        momentum.y = -momentum.y
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        trsa.translate.y += -2 * sprite.rect.top
    elif sprite.rect.bottom > container.bottom and momentum.y > 0:
        momentum.y = -momentum.y
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        trsa.translate.y += 2 * (container.height - sprite.rect.bottom)


def deadzone_system(dt, eid, container, trsa):
    """Kill sprites moving outside defined boundaries

    To avoid sprites flying off to infinity, a dead zone can be defined, that
    should be sufficiently larger than the screen.

    Entities entering that zone (or actually, leaving the container rect) will
    be removed.

    Parameters
    ----------
    container : pygame.rect.Rect
        The boundaries within sprites stay alive.

    trsa : swirlyswirl.compsys.TRSA
        The location of the entity.

    Returns
    -------
    None

    """
    if not container.collidepoint(trsa.translate):
        ecs.remove_entity(eid)
