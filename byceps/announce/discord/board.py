"""
byceps.announce.discord.board
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Announce board events on Discord via its webhooks API.

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import current_app
import requests

from ...events.board import BoardPostingCreated, BoardTopicCreated
from ...services.board.transfer.models import BoardID
from ...services.webhooks import service as webhook_service
from ...signals import board as board_signals
from ...util.jobqueue import enqueue

from ..helpers import get_screen_name_or_fallback


def send_message(scope: str, scope_id: str, text: str) -> None:
    """Send text to the webhook API.

    The endpoint URL already includes the target channel.
    """
    format = 'discord'
    webhook = webhook_service.find_enabled_outgoing_webhook(scope, scope_id, format)
    if webhook is None:
        current_app.logger.warning(
            f'No enabled Discord webhook found for scope "{scope}" and '
            f'scope ID "{scope_id}". Not sending message to Discord.'
        )
        return

    text_prefix = webhook.text_prefix
    if text_prefix:
        text = text_prefix + text

    data = {'content': text}

    requests.post(webhook.url, json=data)  # Ignore response code for now.


# board events


# Note: URLs are wrapped in `<…>` because that prevents
#       preview embedding on Discord.


@board_signals.topic_created.connect
def _on_board_topic_created(sender, *, event: BoardTopicCreated = None) -> None:
    enqueue(announce_board_topic_created, event)


def announce_board_topic_created(event: BoardTopicCreated) -> None:
    """Announce that someone has created a board topic."""
    topic_creator_screen_name = get_screen_name_or_fallback(
        event.topic_creator_screen_name
    )

    text = (
        f'{topic_creator_screen_name} hat das Thema '
        f'"{event.topic_title}" erstellt: <{event.url}>'
    )

    send_board_message(event.board_id, text)


@board_signals.posting_created.connect
def _on_board_posting_created(
    sender, *, event: BoardPostingCreated = None
) -> None:
    enqueue(announce_board_posting_created, event)


def announce_board_posting_created(event: BoardPostingCreated) -> None:
    """Announce that someone has created a board posting."""
    if event.topic_muted:
        return

    posting_creator_screen_name = get_screen_name_or_fallback(
        event.posting_creator_screen_name
    )

    text = (
        f'{posting_creator_screen_name} hat auf das Thema '
        f'"{event.topic_title}" geantwortet: <{event.url}>'
    )

    send_board_message(event.board_id, text)


def send_board_message(board_id: BoardID, text: str) -> None:
    scope = 'board'
    scope_id = str(board_id)

    send_message(scope, scope_id, text)
