"""
byceps.announce.irc.util
~~~~~~~~~~~~~~~~~~~~~~~~

Send messages to an IRC bot (Weitersager_) via HTTP.

.. _Weitersager: https://github.com/homeworkprod/weitersager

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import current_app
import requests

from ...events.base import _BaseEvent
from ...services.webhooks import service as webhook_service
from ...services.webhooks.transfer.models import OutgoingWebhook

from ..visibility import get_visibilities, Visibility

from ._config import CHANNEL_ORGA_LOG, CHANNEL_PUBLIC


CHANNELS_BY_VISIBILITY = {
    Visibility.internal: CHANNEL_ORGA_LOG,
    Visibility.public: CHANNEL_PUBLIC,
}


def send_message(
    event: _BaseEvent, scope: str, scope_id: str, text: str
) -> None:
    """Write the text to the channel(s) appropriate for this event type
    by sending it to the bot via HTTP.
    """
    visibilities = get_visibilities(event)
    if not visibilities:
        current_app.logger.warning(
            f'No visibility assigned for event type "{type(event)}".'
        )
        return

    scope_id = None
    format = 'weitersager'

    webhooks_with_channels = []
    for visibility in visibilities:
        scope = visibility.name

        webhook = webhook_service.find_enabled_outgoing_webhook(
            scope, scope_id, format
        )
        if webhook is None:
            continue

        channel = CHANNELS_BY_VISIBILITY[visibility]

        webhooks_with_channels.append((webhook, channel))

    if not webhooks_with_channels:
        current_app.logger.warning(
            f'No enabled IRC webhooks found. Not sending message to IRC.'
        )
        return

    # Stable order is easier to test.
    webhooks_with_channels.sort(key=lambda xs: xs[1])

    for webhook, channel in webhooks_with_channels:
        call_webhook(webhook, channel, text)


def call_webhook(webhook: OutgoingWebhook, channel: str, text: str) -> None:
    text_prefix = webhook.text_prefix
    if text_prefix:
        text = text_prefix + text

    data = {'channel': channel, 'text': text}

    requests.post(webhook.url, json=data)  # Ignore response code for now.
