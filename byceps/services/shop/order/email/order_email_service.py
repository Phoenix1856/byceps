"""
byceps.services.shop.order.email.order_email_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Notification e-mails about shop orders

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass

from flask_babel import format_date, gettext

from .....services.email import (
    email_config_service,
    email_footer_service,
    email_service,
)
from .....services.email.models import Message
from .....services.shop.order.models.order import Order, OrderID
from .....services.shop.order import order_service
from .....services.shop.shop import shop_service
from .....services.user.models.user import User
from .....services.user import user_service
from .....typing import BrandID
from .....util.l10n import force_user_locale, format_money, get_user_locale

from .. import order_payment_service


@dataclass(frozen=True)
class OrderEmailData:
    order: Order
    brand_id: BrandID
    orderer: User
    orderer_email_address: str
    language_code: str


def send_email_for_incoming_order_to_orderer(order_id: OrderID) -> None:
    data = _get_order_email_data(order_id)

    message = _assemble_email_for_incoming_order_to_orderer(data)

    _send_email(message)


def send_email_for_canceled_order_to_orderer(order_id: OrderID) -> None:
    data = _get_order_email_data(order_id)

    message = _assemble_email_for_canceled_order_to_orderer(data)

    _send_email(message)


def send_email_for_paid_order_to_orderer(order_id: OrderID) -> None:
    data = _get_order_email_data(order_id)

    message = _assemble_email_for_paid_order_to_orderer(data)

    _send_email(message)


def _assemble_email_for_incoming_order_to_orderer(
    data: OrderEmailData,
) -> Message:
    order = data.order
    order_number = order.order_number

    with force_user_locale(data.orderer):
        subject = gettext(
            'Your order (%(order_number)s) has been received.',
            order_number=order_number,
        )

        date_str = format_date(order.created_at)
        indentation = '  '
        line_items = [
            '\n'.join(
                [
                    indentation
                    + gettext('Description')
                    + ': '
                    + line_item.description,
                    indentation
                    + gettext('Quantity')
                    + ': '
                    + str(line_item.quantity),
                    indentation
                    + gettext('Unit price')
                    + ': '
                    + format_money(line_item.unit_price),
                    indentation
                    + gettext('Line price')
                    + ': '
                    + format_money(line_item.line_amount),
                ]
            )
            for line_item in sorted(
                order.line_items, key=lambda li: li.description
            )
        ]
        total_amount = (
            indentation
            + gettext('Total amount')
            + ': '
            + format_money(order.total_amount)
        )
        payment_instructions = (
            order_payment_service.get_email_payment_instructions(
                order, data.language_code
            )
        )
        paragraphs = [
            gettext(
                'thank you for your order %(order_number)s on %(order_date)s through our website.',
                order_number=order_number,
                order_date=date_str,
            ),
            gettext('You have ordered these items:'),
            *line_items,
            total_amount,
            payment_instructions,
        ]
        body = _assemble_body(data, paragraphs)

    recipient_address = data.orderer_email_address

    return _assemble_email_to_orderer(
        subject, body, data.brand_id, recipient_address
    )


def _assemble_email_for_canceled_order_to_orderer(
    data: OrderEmailData,
) -> Message:
    order = data.order
    order_number = order.order_number

    with force_user_locale(data.orderer):
        subject = '\u274c ' + gettext(
            'Your order (%(order_number)s) has been canceled.',
            order_number=order_number,
        )

        date_str = format_date(order.created_at)
        cancelation_reason = order.cancelation_reason or ''
        paragraphs = [
            gettext(
                'your order %(order_number)s on %(order_date)s has been canceled by us for this reason:',
                order_number=order_number,
                order_date=date_str,
            ),
            cancelation_reason,
        ]
        body = _assemble_body(data, paragraphs)

    recipient_address = data.orderer_email_address

    return _assemble_email_to_orderer(
        subject, body, data.brand_id, recipient_address
    )


def _assemble_email_for_paid_order_to_orderer(data: OrderEmailData) -> Message:
    order = data.order
    order_number = order.order_number

    with force_user_locale(data.orderer):
        subject = '\u2705 ' + gettext(
            'Your order (%(order_number)s) has been paid.',
            order_number=order_number,
        )

        date_str = format_date(order.created_at)
        paragraphs = [
            gettext(
                'thank you for your order %(order_number)s on %(order_date)s through our website.',
                order_number=order_number,
                order_date=date_str,
            ),
            gettext(
                'We have received your payment and have marked your order as paid.'
            ),
        ]
        body = _assemble_body(data, paragraphs)

    recipient_address = data.orderer_email_address

    return _assemble_email_to_orderer(
        subject, body, data.brand_id, recipient_address
    )


def _get_order_email_data(order_id: OrderID) -> OrderEmailData:
    """Collect data required for an order e-mail template."""
    order = order_service.get_order(order_id)

    shop = shop_service.get_shop(order.shop_id)
    orderer_id = order.placed_by_id
    orderer = user_service.get_user(orderer_id)
    email_address = user_service.get_email_address(orderer_id)
    language_code = get_user_locale(orderer)

    return OrderEmailData(
        order=order,
        brand_id=shop.brand_id,
        orderer=orderer,
        orderer_email_address=email_address,
        language_code=language_code,
    )


def _assemble_body(data: OrderEmailData, paragraphs: list[str]) -> str:
    """Assemble the plain text part of the email."""
    screen_name = data.orderer.screen_name or 'UnknownUser'
    salutation = gettext('Hello %(screen_name)s,', screen_name=screen_name)
    footer = email_footer_service.get_footer(data.brand_id, data.language_code)

    return '\n\n'.join([salutation] + paragraphs + [footer])


def _assemble_email_to_orderer(
    subject: str,
    body: str,
    brand_id: BrandID,
    recipient_address: str,
) -> Message:
    """Assemble an email message with the rendered template as its body."""
    config = email_config_service.get_config(brand_id)
    sender = config.sender
    recipients = [recipient_address]

    return Message(sender, recipients, subject, body)


def _send_email(message: Message) -> None:
    email_service.enqueue_message(message)
