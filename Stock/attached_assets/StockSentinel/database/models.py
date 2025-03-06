from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    watchlist = relationship('WatchlistItem', back_populates='user')

class WatchlistItem(Base):
    __tablename__ = 'watchlist_items'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String, nullable=False)
    added_date = Column(DateTime, nullable=False)
    target_price = Column(Float, nullable=True)  # Optional price target
    user = relationship('User', back_populates='watchlist')

class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    @classmethod
    def from_yfinance(cls, symbol, data):
        """Create StockData instance from yfinance data"""
        return cls(
            symbol=symbol,
            date=data.name,  # Index in yfinance data is the date
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            volume=data['Volume']
        )

# Database setup
def init_db():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()