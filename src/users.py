'''
great
'''
from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship
from . import db
from . import utils

# make pylint STFU
# pylint: disable=too-few-public-methods

class User(db.Base):
    '''
    represents a user in the database with their credentials
    '''
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)  # salted
    token = Column(String, nullable=True)  # session token, random string
    asahi = Column(Integer, default=0)
    items = relationship("UserItem", back_populates="user")

def get_user_or_rollback(username, session):
    '''
    gets the user.
    rolls back the transaction and throws NoResultFound on failure
    '''
    try:
        user = session.query(User) \
            .filter_by(username=username) \
            .one()
        return user
    except NoResultFound as e:
        print("user does not exist")
        session.rollback()
        raise e

@utils.db_transaction
def create_user(username: str, plaintext_password: str, session=None):
    '''
    adds a new user to the DB
    '''
    usr = User(
        username=username,
        password=utils.encrypt(plaintext_password.encode()),
        token=None
    )
    session.add(usr)

@utils.db_transaction
def delete_user(username, session=None):
    '''
    remove user with username from the DB
    '''
    usr = get_user_or_rollback(username, session)
    session.delete(usr)

@utils.db_transaction
def change_token(username, token, session=None):
    '''
    doing thing
    '''
    usr = get_user_or_rollback(username, session)
    usr.token = token  # 100% certain this can't fail
    return token

# no transaction, it's not needed
def is_token_correct(usr, token):
    '''checks if the token for the user is the token currently on the DB'''
    return usr.token == token

@utils.db_transaction
def authenticate(username, plaintext_password, session=None):
    '''
    thing
    '''
    usr = get_user_or_rollback(username, session)
    ok = utils.check(plaintext_password.encode(), usr.password)
    new_tok = change_token(username, utils.gentoken())
    if not ok:
        raise utils.UnauthorizedError()

    usr.token = new_tok
    return usr.token if ok else None

@utils.db_transaction
def deauthenticate(username, token, session=None):
    '''
    thing
    '''
    usr = get_user_or_rollback(username, session)
    ok = is_token_correct(usr, token)
    if not ok:
        raise utils.UnauthorizedError()

    # assuming it's OK
    usr.token = None

@utils.db_transaction
def change_password(username, password, token, session=None):
    '''
    changes `username`'s password
    '''
    usr = get_user_or_rollback(username, session)
    ok = is_token_correct(usr, token)
    if not ok:
        raise utils.UnauthorizedError()

    usr.password = utils.encrypt(password.encode())
    return usr.password  # return the new password
