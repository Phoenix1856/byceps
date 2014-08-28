# -*- coding: utf-8 -*-

from byceps.blueprints.board.models import Category, Posting, Topic

from .util import add_to_database


@add_to_database
def create_category(brand, position, title, description):
    return Category(brand=brand, position=position, title=title, description=description)


def get_first_category(brand):
    return Category.query.filter_by(brand=brand).filter_by(position=1).one()


@add_to_database
def create_topic(category, creator, title, body):
    return Topic.create(category, creator, title, body)


@add_to_database
def create_posting(topic, creator, body):
    return Posting.create(topic, creator, body)
