'''
ORM base stuff
'''
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
Base = declarative_base()

DBURL = "sqlite:///primary.db"

_engine = None

def engine():
    '''
    get an Engine
    '''
    if not _engine:
        return create_engine(DBURL)
    else:
        return _engine

def session():
    '''
    get a session
    '''
    return sessionmaker(bind=engine())()

def transaction():
    '''
    starts a new transaction and returns it's session
    '''
    return session().begin().session

def create_all_tables():
    '''
    initializes all tables
    '''
    Base.metadata.create_all(engine())
