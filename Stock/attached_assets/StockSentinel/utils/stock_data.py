# Copyright © 2025 Sami Singh. All rights reserved.

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.models import get_session
from database import crud

def get_stock_data(symbol, period='1y'):
    """
    Fetch stock data from database or Yahoo Finance
    """
    try:
        # Create Ticker object
        stock = yf.Ticker(symbol)

        # Get historical data
        hist = stock.history(period=period)

        if hist.empty:
            print(f"No data available for symbol: {symbol}")
            return None, None

        # Get company info
        try:
            info = stock.info
        except Exception as e:
            print(f"Error fetching company info: {str(e)}")
            info = {}

        # Ensure all required columns exist
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in hist.columns for col in required_columns):
            print(f"Missing required columns in data for {symbol}")
            return None, None

        # Save to database if configured
        try:
            db = get_session()
            crud.save_stock_data(db, symbol, hist)
        except Exception as e:
            print(f"Database error: {str(e)}")
            # Continue even if database save fails

        return hist, info

    except Exception as e:
        print(f"Error fetching stock data: {str(e)}")
        return None, None

def get_key_metrics(info):
    """Extract key financial metrics from stock info"""
    metrics = {}

    try:
        metrics = {
            'Market Cap': format_market_cap(info.get('marketCap')),
            'PE Ratio': format_number(info.get('trailingPE')),
            'EPS': format_number(info.get('trailingEps')),
            '52 Week High': format_price(info.get('fiftyTwoWeekHigh')),
            '52 Week Low': format_price(info.get('fiftyTwoWeekLow')),
            'Volume': format_volume(info.get('volume')),
        }
    except Exception as e:
        print(f"Error formatting metrics: {str(e)}")
        # Return empty metrics on error
        metrics = {k: 'N/A' for k in ['Market Cap', 'PE Ratio', 'EPS', '52 Week High', '52 Week Low', 'Volume']}

    return metrics

def format_market_cap(value):
    """Format market cap to billions/millions"""
    if not isinstance(value, (int, float)):
        return 'N/A'
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:,.0f}"

def format_number(value):
    """Format numerical values"""
    if not isinstance(value, (int, float)) or np.isnan(value):
        return 'N/A'
    return f"{value:.2f}"

def format_price(value):
    """Format price values"""
    if not isinstance(value, (int, float)) or np.isnan(value):
        return 'N/A'
    return f"${value:.2f}"

def format_volume(value):
    """Format volume values"""
    if not isinstance(value, (int, float)) or np.isnan(value):
        return 'N/A'
    return f"{value:,.0f}"

def calculate_technical_indicators(df):
    """Calculate technical indicators for the stock"""
    try:
        # Ensure DataFrame is not empty
        if df.empty:
            return df

        # Basic Moving Averages
        df['SMA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        df['SMA50'] = df['Close'].rolling(window=50, min_periods=1).mean()

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']

        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20, min_periods=1).mean()
        std = df['Close'].rolling(window=20, min_periods=1).std()
        df['BB_upper'] = df['BB_middle'] + 2 * std
        df['BB_lower'] = df['BB_middle'] - 2 * std

        # Fill NaN values with first valid observation
        df.fillna(method='bfill', inplace=True)

        return df

    except Exception as e:
        print(f"Error calculating technical indicators: {str(e)}")
        return df

def get_stock_news(symbol):
    """Get news articles for a stock"""
    try:
        stock = yf.Ticker(symbol)
        news = stock.news
        return news[:5] if news else []  # Return top 5 news items
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return []