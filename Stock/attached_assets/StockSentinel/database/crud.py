from datetime import datetime
from sqlalchemy.orm import Session
from . import models

def create_user(db: Session, email: str):
    user = models.User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def add_to_watchlist(db: Session, user_id: int, symbol: str):
    watchlist_item = models.WatchlistItem(
        user_id=user_id,
        symbol=symbol,
        added_date=datetime.now()
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item

def save_stock_data(db: Session, symbol: str, yf_data):
    """Save stock data from yfinance to database"""
    for date, row in yf_data.iterrows():
        stock_data = models.StockData.from_yfinance(symbol, row)
        db.add(stock_data)
    db.commit()

def get_stock_data(db: Session, symbol: str, start_date: datetime = None):
    """Retrieve stock data from database"""
    query = db.query(models.StockData).filter(models.StockData.symbol == symbol)
    if start_date:
        query = query.filter(models.StockData.date >= start_date)
    return query.order_by(models.StockData.date).all()
