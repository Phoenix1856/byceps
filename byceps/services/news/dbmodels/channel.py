"""
byceps.services.news.dbmodels.channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from typing import Optional

from ....database import db
from ....typing import BrandID
from ....util.instances import ReprBuilder

from ...site.models import SiteID

from ..models import NewsChannelID


class DbNewsChannel(db.Model):
    """A channel to which news items can be published."""

    __tablename__ = 'news_channels'

    id = db.Column(db.UnicodeText, primary_key=True)
    brand_id = db.Column(
        db.UnicodeText, db.ForeignKey('brands.id'), index=True, nullable=False
    )
    announcement_site_id = db.Column(
        db.UnicodeText, db.ForeignKey('sites.id'), nullable=True
    )
    archived = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(
        self,
        channel_id: NewsChannelID,
        brand_id: BrandID,
        *,
        announcement_site_id: Optional[SiteID] = None,
    ) -> None:
        self.id = channel_id
        self.brand_id = brand_id
        self.announcement_site_id = announcement_site_id

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add_with_lookup('id')
            .add('brand', self.brand_id)
            .build()
        )
