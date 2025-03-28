"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from unittest.mock import patch

from flask import Flask
import pytest

from byceps.events.ticketing import TicketsSold
from byceps.services.shop.article.models import Article
from byceps.services.shop.order.models.order import Order, Orderer
from byceps.services.shop.order import (
    order_action_registry_service,
    order_log_service,
)
from byceps.services.shop.shop.models import Shop
from byceps.services.shop.storefront.models import Storefront
from byceps.services.ticketing.dbmodels.ticket import DbTicket
from byceps.services.ticketing.models.ticket import TicketCategory
from byceps.services.ticketing import ticket_service, ticket_bundle_service
from byceps.services.user.models.user import User

from .helpers import get_tickets_for_order, mark_order_as_paid, place_order


@pytest.fixture
def article(make_article, shop: Shop) -> Article:
    return make_article(shop.id)


@pytest.fixture(scope='module')
def ticket_quantity_per_bundle() -> int:
    return 5


@pytest.fixture(scope='module')
def bundle_quantity() -> int:
    return 2


@pytest.fixture
def order(
    article: Article,
    bundle_quantity: int,
    storefront: Storefront,
    orderer: Orderer,
) -> Order:
    articles_with_quantity = [(article, bundle_quantity)]
    return place_order(storefront.id, orderer, articles_with_quantity)


@pytest.fixture
def order_action(
    article: Article,
    ticket_category: TicketCategory,
    ticket_quantity_per_bundle: int,
) -> None:
    order_action_registry_service.register_ticket_bundles_creation(
        article.id,
        ticket_category.id,
        ticket_quantity_per_bundle,
    )


@patch('byceps.signals.ticketing.tickets_sold.send')
def test_create_ticket_bundles(
    tickets_sold_signal_send_mock,
    admin_app: Flask,
    article: Article,
    ticket_category: TicketCategory,
    ticket_quantity_per_bundle: int,
    bundle_quantity: int,
    admin_user: User,
    orderer_user: User,
    orderer: Orderer,
    order: Order,
    order_action,
) -> None:
    expected_ticket_total = 10

    tickets_before_paid = get_tickets_for_order(order)
    assert len(tickets_before_paid) == 0

    shop_order_paid_event = mark_order_as_paid(order.id, admin_user.id)

    tickets_after_paid = get_tickets_for_order(order)
    assert len(tickets_after_paid) == expected_ticket_total

    for ticket in tickets_after_paid:
        assert ticket.owned_by_id == orderer.user_id
        assert ticket.used_by_id == orderer.user_id

    log_entries = order_log_service.get_entries_for_order(order.id)
    ticket_bundle_created_log_entries = [
        entry
        for entry in log_entries
        if entry.event_type == 'ticket-bundle-created'
    ]
    assert len(ticket_bundle_created_log_entries) == bundle_quantity

    tickets_sold_event = TicketsSold(
        occurred_at=shop_order_paid_event.occurred_at,
        initiator_id=admin_user.id,
        initiator_screen_name=admin_user.screen_name,
        party_id=ticket_category.party_id,
        owner_id=orderer_user.id,
        owner_screen_name=orderer_user.screen_name,
        quantity=expected_ticket_total,
    )
    tickets_sold_signal_send_mock.assert_called_once_with(
        None, event=tickets_sold_event
    )

    tear_down_bundles(tickets_after_paid)


# helpers


def tear_down_bundles(tickets: list[DbTicket]) -> None:
    bundle_ids = {t.bundle_id for t in tickets}

    for ticket in tickets:
        ticket_service.delete_ticket(ticket.id)

    for bundle_id in bundle_ids:
        ticket_bundle_service.delete_bundle(bundle_id)
