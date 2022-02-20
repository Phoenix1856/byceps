"""
:Copyright: 2006-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from typing import Optional

import pytest

from byceps.services.news import channel_service
from byceps.services.news.transfer.models import Channel, ChannelID
from byceps.typing import BrandID

from tests.helpers import generate_token


@pytest.fixture
def make_channel():
    def _wrapper(
        brand_id: BrandID,
        channel_id: Optional[ChannelID] = None,
        *,
        url_prefix: Optional[str] = None,
    ) -> Channel:
        if channel_id is None:
            channel_id = ChannelID(generate_token())

        return channel_service.create_channel(
            brand_id, channel_id, url_prefix=url_prefix
        )

    return _wrapper
