# -*- coding: utf-8 -*-

"""
byceps.services.user_avatar.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import abort

from ...database import db
from ...util.image import create_thumbnail, read_dimensions
from ...util.image.models import Dimensions, ImageType
from ...util.image.typeguess import guess_type
from ...util import upload

from .models import Avatar, AvatarSelection


ALL_IMAGE_TYPES = frozenset(ImageType)

MAXIMUM_DIMENSIONS = Dimensions(512, 512)


def get_image_type_names(types):
    """Return the names of the image types."""
    return frozenset(t.name.upper() for t in types)


def update_avatar_image(user, stream, *, allowed_types=ALL_IMAGE_TYPES,
                        maximum_dimensions=MAXIMUM_DIMENSIONS):
    """Set a new avatar image for the user."""
    image_type = _determine_image_type(stream, allowed_types)

    if _is_image_too_large(stream, maximum_dimensions):
        stream = create_thumbnail(stream, image_type.name, maximum_dimensions)

    avatar = Avatar(user.id, image_type)
    db.session.add(avatar)
    db.session.commit()

    # Might raise `FileExistsError`.
    upload.store(stream, avatar.path)

    user.avatar = avatar
    db.session.commit()


def _determine_image_type(stream, allowed_types):
    image_type = guess_type(stream)

    if image_type not in allowed_types:
        allowed_type_names = get_image_type_names(allowed_types)
        allowed_type_names_string = ', '.join(sorted(allowed_type_names))

        abort(400, 'Only images of these types are allowed: {}'
            .format(allowed_type_names_string))

    stream.seek(0)
    return image_type


def _is_image_too_large(stream, maximum_dimensions):
    actual_dimensions = read_dimensions(stream)
    stream.seek(0)
    return actual_dimensions > maximum_dimensions


def remove_avatar_image(user):
    """Remove the user's avatar image.

    The avatar will be unlinked from the user, but the database record
    as well as the image file itself won't be removed, though.
    """
    db.session.delete(user.avatar_selection)
    db.session.commit()


def get_avatars_for_user(user_id):
    """Return all avatars uploaded by the user."""
    return Avatar.query \
        .filter_by(creator_id=user_id) \
        .all()


def get_avatar_for_user(user_id):
    """Return the user's current avatar."""
    avatars_by_user_id = get_avatars_for_users({user_id})
    return avatars_by_user_id[user_id]


def get_avatars_for_users(user_ids):
    """Return the those users' current avatars."""
    urls_by_user_id = get_avatar_urls_for_users(user_ids)

    avatars_by_user_id = {}

    for user_id in user_ids:
        avatar = {}

        url = urls_by_user_id.get(user_id)
        if url:
            avatar['url'] = url

        avatars_by_user_id[user_id] = avatar

    return avatars_by_user_id


def get_avatar_urls_for_users(user_ids):
    """Return the URLs of those users' current avatars."""
    selections = AvatarSelection.query \
        .options(db.joinedload('avatar')) \
        .filter(AvatarSelection.user_id.in_(user_ids)) \
        .all()

    return {selection.user_id: selection.avatar.url for selection in selections}
