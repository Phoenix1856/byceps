"""
byceps.services.shop.order.actions.award_badge
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from .....typing import UserID

from ....user_badge.models import BadgeAwarding
from ....user_badge import user_badge_awarding_service, user_badge_service

from ..models.action import ActionParameters
from ..models.order import LineItem, Order, OrderID
from .. import order_log_service


def award_badge(
    order: Order,
    line_item: LineItem,
    initiator_id: UserID,
    parameters: ActionParameters,
) -> None:
    """Award badge to user."""
    badge = user_badge_service.get_badge(parameters['badge_id'])
    user_id = order.placed_by_id

    for _ in range(line_item.quantity):
        awarding, _ = user_badge_awarding_service.award_badge_to_user(
            badge.id, user_id
        )

        _create_order_log_entry(order.id, awarding)


def _create_order_log_entry(order_id: OrderID, awarding: BadgeAwarding) -> None:
    event_type = 'badge-awarded'
    data = {
        'awarding_id': str(awarding.id),
        'badge_id': str(awarding.badge_id),
        'recipient_id': str(awarding.user_id),
    }

    order_log_service.create_entry(event_type, order_id, data)
