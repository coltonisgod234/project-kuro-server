'''
ORM base stuff
'''
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
Base = declarative_base()

DBURL = "sqlite:///primary.db"

def engine():
    '''
    get an Engine
    '''
    return create_engine(DBURL)

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
