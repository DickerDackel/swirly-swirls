import pygame
import tinyecs as ecs


def container_system(dt, eid, container, position, momentum, angular_momentum, sprite):
    """A system to make a sprite bonce off the edges of the screen.

    This is not of use for actual programs, but it's a nice example of a custom
    component.  It can still be used in test programs if you need to manage
    your sprites on screen.

    Parameters
    ----------
    container : pygame.Rect
        The bounding box for the sprites
    position: pygame.Vector2
        World position and state of the sprite.  If a wall is hit, the position
        will be reset to inside the container.
    momentum
        The momentum of the sprite.  On wall hit, it is inversed on the
        collision axis.
    angular_momentun : float
        The angular momentum of the sprite.  Reversed on wall hits.
    sprite : tinyecs.components.ESprite
        The visualization of the entity, a.k.a. the sprite to bounce around.

    Returns
    -------
    None

    """
    if sprite.rect.left < container.left and momentum.x < 0:
        momentum.x = -momentum.x
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        position.x += -2 * sprite.rect.left
    elif sprite.rect.right > container.right and momentum.x > 0:
        momentum.x = -momentum.x
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        position.x += 2 * (container.width - sprite.rect.right)

    if sprite.rect.top < container.top and momentum.x < 0:
        momentum.y = -momentum.y
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        position.y += -2 * sprite.rect.top
    elif sprite.rect.bottom > container.bottom and momentum.y > 0:
        momentum.y = -momentum.y
        ecs.add_component(eid, 'angular-momentum', -angular_momentum)
        position.y += 2 * (container.height - sprite.rect.bottom)
