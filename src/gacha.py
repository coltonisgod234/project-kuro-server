'''
gacha system
'''
# pylint: disable=unused-import
# pylint: disable=too-few-public-methods
import random
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Session
from . import db
from . import utils
from .users import User

class UserItem(db.Base):
    '''
    represents a user's characters
    '''
    __tablename__ = "user_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="items")

class NotEnoughAsahi(Exception): '''thrown when there's not enough asahi to pull'''

@utils.db_transaction
def remove(username: str, name: str, session: Session = None):
    '''
    removes a user's item by ID
    '''
    obj = session.query(UserItem) \
        .join(User) \
        .where(User.username == username) \
        .where(UserItem.name == name) \
        .one()

    session.delete(obj)

@utils.db_transaction
def grant(username: str, item_name: str, session: Session = None):
    '''
    grant an item
    '''
    user = session.query(User) \
        .where(User.username == username) \
        .one()

    obj = UserItem(
        name = item_name,
        user = user
    )

    session.add(obj)
    session.flush()  # ugly but it's gotta happen
    return obj.id

@utils.db_transaction
def pull1(user: User, banner_data: dict, session: Session = None):
    '''
    Pulls for an item on a banner
    '''
    cost = banner_data["pull_cost"]
    if user.asahi < cost:
        raise NotEnoughAsahi

    user.asahi -= cost
    drops = banner_data["drops"]
    drop = random.choices(
        drops,
        weights = [e["weight"] for e in drops],
        k = 1
    )[0]
    _id = grant(
        username = user.username,
        item_name = drop["item"]
    )
    return _id, drop
