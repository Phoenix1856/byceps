# -*- coding: utf-8 -*-

"""
byceps.blueprints.shop.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2015 Jochen Kupperschmidt
"""

from wtforms import DateField, SelectField, StringField
from wtforms.validators import InputRequired, Length

from ...util.l10n import LocalizedForm

from .models import Cart, CartItem, Orderer


class OrderForm(LocalizedForm):
    first_names = StringField('Vorname(n)', validators=[Length(min=2)])
    last_name = StringField('Nachname', validators=[Length(min=2)])
    date_of_birth = DateField('Geburtsdatum', format='%d.%m.%Y', validators=[InputRequired()])
    zip_code = StringField('PLZ', validators=[Length(min=5, max=5)])
    city = StringField('Stadt', validators=[Length(min=2)])
    street = StringField('Straße', validators=[Length(min=2)])

    def get_orderer(self, user):
        return Orderer(
            user,
            self.first_names.data.strip(),
            self.last_name.data.strip(),
            self.date_of_birth.data,
            self.zip_code.data.strip(),
            self.city.data.strip(),
            self.street.data.strip(),
        )


def assemble_articles_order_form(articles):
    """Dynamically extend the order form with one field per article."""

    class ArticlesOrderForm(OrderForm):

        def get_cart(self, articles):
            cart = Cart()
            for item in self.get_cart_items(articles):
                cart.add_item(item)
            return cart

        def get_cart_items(self, article_compilation):
            for item in article_compilation.get_items():
                field_name = 'article_{}'.format(item.article.id)
                field = getattr(self, field_name)
                quantity = field.data
                if quantity > 0:
                    yield CartItem(item.article, quantity)


    validators = [InputRequired()]
    for article in articles:
        field_name = 'article_{}'.format(article.id)
        choices = _create_choices(article)
        field = SelectField('Anzahl', validators, coerce=int, choices=choices)
        setattr(ArticlesOrderForm, field_name, field)

    return ArticlesOrderForm


def _create_choices(article):
    max_orderable_quantity = _get_max_orderable_quantity(article)
    quantities = list(range(max_orderable_quantity + 1))
    return [(quantity, str(quantity)) for quantity in quantities]


def _get_max_orderable_quantity(article):
    if article.max_quantity_per_order is None:
        return article.quantity

    return min(article.quantity, article.max_quantity_per_order)
