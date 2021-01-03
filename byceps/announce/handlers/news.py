"""
byceps.announce.handlers.news
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Announce news events.

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from ...events.news import NewsItemPublished
from ...services.webhooks.transfer.models import OutgoingWebhook
from ...util.jobqueue import enqueue_at

from ..helpers import call_webhook, matches_selectors
from ..text_assembly import news


def announce_news_item_published(
    event: NewsItemPublished, webhook: OutgoingWebhook
) -> None:
    """Announce that a news item has been published."""
    text = news.assemble_text_for_news_item_published(event)

    if event.published_at > event.occurred_at:
        # Schedule job to announce later.
        enqueue_at(event.published_at, send_news_message, event, webhook, text)
    else:
        # Announce now.
        send_news_message(event, webhook, text)


# helpers


def send_news_message(
    event: NewsItemPublished, webhook: OutgoingWebhook, text: str
) -> None:
    channel_id = str(event.channel_id)
    if not matches_selectors(event, webhook, 'channel_id', channel_id):
        return

    call_webhook(webhook, text)
