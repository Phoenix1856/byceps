"""
byceps.services.shop.storefront.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass
from typing import NewType, Optional

from ..catalog.models import CatalogID
from ..order.models.number import OrderNumberSequenceID
from ..shop.models import ShopID


StorefrontID = NewType('StorefrontID', str)


@dataclass(frozen=True)
class Storefront:
    id: StorefrontID
    shop_id: ShopID
    catalog_id: Optional[CatalogID]
    order_number_sequence_id: OrderNumberSequenceID
    closed: bool
