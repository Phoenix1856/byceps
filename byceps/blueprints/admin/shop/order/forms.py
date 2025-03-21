"""
byceps.blueprints.admin.shop.order.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext
from wtforms import BooleanField, RadioField, StringField, TextAreaField
from wtforms.validators import InputRequired, Length

from .....services.shop.order import order_service
from .....services.shop.order.models.order import PAYMENT_METHODS
from .....util.l10n import LocalizedForm


class AddNoteForm(LocalizedForm):
    text = TextAreaField(lazy_gettext('Text'), validators=[InputRequired()])


class CancelForm(LocalizedForm):
    reason = TextAreaField(
        lazy_gettext('Reason'),
        validators=[InputRequired(), Length(max=1000)],
    )
    send_email = BooleanField(
        lazy_gettext('Actively inform orderer via email of cancelation')
    )


def _get_payment_method_choices():
    choices = [
        (pm, order_service.find_payment_method_label(pm) or pm)
        for pm in PAYMENT_METHODS
    ]
    choices.sort()
    return choices


class MarkAsPaidForm(LocalizedForm):
    payment_method = RadioField(
        lazy_gettext('Payment type'),
        choices=_get_payment_method_choices(),
        default='bank_transfer',
        validators=[InputRequired()],
    )


class OrderNumberSequenceCreateForm(LocalizedForm):
    prefix = StringField(
        lazy_gettext('Static prefix'), validators=[InputRequired()]
    )
