"""
byceps.util.irc
~~~~~~~~~~~~~~~

Send IRC messages to a bot via HTTP.

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from time import sleep
from typing import Optional

from flask import current_app
import requests

from ..services.global_setting import service as global_settings_service


def send_message(channel: str, text: str) -> None:
    """Write the text to the channel by sending it to the bot via HTTP."""
    if not _is_enabled():
        current_app.logger.warning('Announcements on IRC are disabled.')
        return

    url = _get_webhook_url()
    if not url:
        current_app.logger.warning(
            'No webhook URL configured for announcements on IRC.'
        )
        return

    text_prefix = _get_text_prefix()
    if text_prefix:
        text = text_prefix + text

    data = {'channel': channel, 'text': text}

    # Delay a bit as an attempt to avoid getting kicked from server
    # because of flooding.
    delay = _get_delay()
    sleep(delay)

    requests.post(url, json=data)  # Ignore response code for now.


def _is_enabled() -> bool:
    """Return `true' if announcements on IRC are enabled.

    Disabled by default.
    """
    value = global_settings_service.find_setting_value('announce_irc_enabled')
    return value == 'true'


def _get_webhook_url() -> Optional[str]:
    """Return the configured webhook URL."""
    return global_settings_service.find_setting_value(
        'announce_irc_webhook_url'
    )


def _get_text_prefix() -> Optional[str]:
    """Return the configured text prefix."""
    return global_settings_service.find_setting_value(
        'announce_irc_text_prefix'
    )


def _get_delay(default: int = 2) -> int:
    """Return the configured delay, in seconds."""
    value_str = global_settings_service.find_setting_value('announce_irc_delay')
    if value_str is None:
        return default

    try:
        value = int(value_str)
    except (TypeError, ValueError) as e:
        current_app.logger.warning(
            f'Invalid delay value configured for announcements on IRC: {e}'
        )
        return default

    return value
