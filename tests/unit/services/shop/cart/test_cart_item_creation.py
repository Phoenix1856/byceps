"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from decimal import Decimal

from moneyed import EUR, Money
import pytest
from pytest import raises

from byceps.database import generate_uuid4
from byceps.services.shop.article.models import (
    Article,
    ArticleID,
    ArticleNumber,
    ArticleType,
)
from byceps.services.shop.cart.models import CartItem
from byceps.services.shop.shop.models import ShopID


@pytest.mark.parametrize(
    'quantity, expected_line_amount',
    [
        (1, Money('1.99', EUR)),
        (2, Money('3.98', EUR)),
        (6, Money('11.94', EUR)),
    ],
)
def test_init_with_positive_quantity(
    quantity: int, expected_line_amount: Money
):
    item = create_item(quantity)

    assert item.quantity == quantity
    assert item.line_amount == expected_line_amount


def test_init_with_zero_quantity():
    with raises(ValueError):
        create_item(0)


def test_init_with_negative_quantity():
    with raises(ValueError):
        create_item(-1)


# helpers


def create_item(quantity: int) -> CartItem:
    article = create_article()
    return CartItem(article, quantity)


def create_article() -> Article:
    return Article(
        id=ArticleID(generate_uuid4()),
        shop_id=ShopID('any-shop'),
        item_number=ArticleNumber('article-123'),
        type_=ArticleType.other,
        type_params={},
        description='Cool thing',
        price=Money('1.99', EUR),
        tax_rate=Decimal('0.19'),
        available_from=None,
        available_until=None,
        total_quantity=1,
        quantity=1,
        max_quantity_per_order=1,
        not_directly_orderable=False,
        separate_order_required=False,
        processing_required=False,
    )
