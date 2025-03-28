"""
byceps.services.board.board_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from typing import Optional

from sqlalchemy import delete, select

from ...database import db
from ...typing import BrandID

from ..brand import brand_service

from .dbmodels.board import DbBoard
from .models import Board, BoardID


def create_board(brand_id: BrandID, board_id: BoardID) -> Board:
    """Create a board for that brand."""
    brand = brand_service.find_brand(brand_id)
    if brand is None:
        raise ValueError(f'Unknown brand ID "{brand_id}"')

    db_board = DbBoard(board_id, brand.id)

    db.session.add(db_board)
    db.session.commit()

    return _db_entity_to_board(db_board)


def delete_board(board_id: BoardID) -> None:
    """Delete a board."""
    db.session.execute(delete(DbBoard).filter_by(id=board_id))
    db.session.commit()


def find_board(board_id: BoardID) -> Optional[Board]:
    """Return the board with that id, or `None` if not found."""
    db_board = db.session.get(DbBoard, board_id)

    if db_board is None:
        return None

    return _db_entity_to_board(db_board)


def get_boards_for_brand(brand_id: BrandID) -> list[Board]:
    """Return all boards that belong to the brand."""
    db_boards = db.session.scalars(
        select(DbBoard).filter_by(brand_id=brand_id)
    ).all()

    return [_db_entity_to_board(db_board) for db_board in db_boards]


def _db_entity_to_board(db_board: DbBoard) -> Board:
    return Board(
        id=db_board.id,
        brand_id=db_board.brand_id,
        access_restricted=db_board.access_restricted,
    )
