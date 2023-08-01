import pygame
import tinyecs as ecs


class EVSprite(pygame.sprite.Sprite):
    """A sprite class especially for ECS entities.

    The E stands for the ECS, the V for virtual sprite.

    If an entity with a sprite component is removed, the sprite also needs to
    be removed from all sprite groups.

    `tinyecs` offers the `shutdown_` method for this.  If this is available,
    ecs.remove_entity will call it when tearing down an entity.

    The "virtual" part of this entity is the image access.  The image is just
    a property that calls a factory function instead.  That way, image
    generation can be handed over to a different component.  The sprite itself
    is only responsible to provide a link to the sprite group, which handles
    the drawing.

    Parameters
    ----------
    image_factory: callable
        A zero parameter function that is expected to return a
        `pygame.surface.Surface` object.

    *groups: *pygame.sprite.Group()
        Directly passed into parent class.  See `pygame.sprite.Sprite` for
        details.

    """
    def __init__(self, image_factory, *groups):
        super().__init__(*groups)
        self.image_factory = image_factory

        self._image = pygame.surface.Surface((1, 1))
        self.rect = self._image.get_rect(bottomright=(-1, -1))

    def shutdown_(self):
        self.kill()

    @property
    def image(self):
        new_image = self.image_factory.image
        if new_image is self._image:
            return self._image
        else:
            self._image = new_image
            self.rect = self._image.get_rect(center=self.rect.center)

        return self._image

    @image.setter
    def image(self, image):
        raise RuntimeError('EVSprite.image is dynamically generated.')


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
    def __init__(self, *groups, tag=None, image=None):
        super().__init__(*groups)

        if image is None:
            self.image = pygame.surface.Surface((1, 1))
        else:
            self.image = image

        self.rect = self.image.get_rect(bottomright=(-1, -1))

    def shutdown_(self):
        self.kill()


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
    sprite : swirlyswirl.compsys.ESprite
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
