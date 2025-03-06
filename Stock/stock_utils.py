import yfinance as yf
import pandas as pd
import numpy as np
from database import get_db_connection
import websocket
import json
import threading
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import requests

def get_real_time_price(symbol):
    """Get real-time price data with fallback mechanisms"""
    # Try getting from database first
    price_data = get_stored_real_time_price(symbol)
    if price_data:
        return price_data

    # Fallback to yfinance if database data is not fresh
    try:
        ticker = yf.Ticker(symbol)
        current_data = ticker.history(period='1d', interval='1m').iloc[-1]
        price_data = {
            'price': float(current_data['Close']),
            'volume': int(current_data['Volume']),
            'timestamp': datetime.now()
        }
        # Store in database for future use
        store_real_time_price(symbol, price_data['price'], price_data['volume'])
        return price_data
    except Exception as e:
        print(f"Error fetching real-time price for {symbol}: {e}")
        return None

def store_real_time_price(symbol, price, volume):
    """Store real-time price in database with error handling"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO real_time_prices (symbol, price, volume)
                VALUES (%s, %s, %s)
                ON CONFLICT (symbol) 
                DO UPDATE SET 
                    price = %s, 
                    volume = %s, 
                    timestamp = CURRENT_TIMESTAMP
            ''', (symbol, price, volume, price, volume))
            conn.commit()
    except Exception as e:
        print(f"Error storing real-time price: {e}")

def get_stored_real_time_price(symbol):
    """Get real-time price from database with freshness check"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price, volume, timestamp 
                FROM real_time_prices 
                WHERE symbol = %s AND 
                      timestamp > NOW() - INTERVAL '1 minute'
            ''', (symbol,))
            result = cursor.fetchone()
            if result:
                return {
                    'price': float(result[0]),
                    'volume': int(result[1]),
                    'timestamp': result[2]
                }
    except Exception as e:
        print(f"Error fetching stored real-time price: {e}")
    return None

def update_stock_prices():
    """Background task to update stock prices"""
    while True:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Get all unique symbols from watchlist and portfolio
                cursor.execute('''
                    SELECT DISTINCT symbol 
                    FROM (
                        SELECT symbol FROM watchlist
                        UNION
                        SELECT symbol FROM portfolio
                    ) AS symbols
                ''')
                symbols = [row[0] for row in cursor.fetchall()]

                # Update prices for each symbol
                for symbol in symbols:
                    try:
                        ticker = yf.Ticker(symbol)
                        current_data = ticker.history(period='1d', interval='1m').iloc[-1]
                        store_real_time_price(
                            symbol,
                            float(current_data['Close']),
                            int(current_data['Volume'])
                        )
                    except Exception as e:
                        print(f"Error updating price for {symbol}: {e}")
                        continue

        except Exception as e:
            print(f"Error in price update loop: {e}")

        # Wait before next update
        time.sleep(60)  # Update every minute

# Start the background price update thread
def start_price_updates():
    """Start the background price update thread"""
    update_thread = threading.Thread(target=update_stock_prices)
    update_thread.daemon = True
    update_thread.start()

def on_message(ws, message):
    """Handle incoming websocket messages"""
    try:
        data = json.loads(message)
        if 'data' in data:
            for quote in data['data']:
                symbol = quote['s']
                price = float(quote['p'])
                volume = int(quote.get('v', 0))
                store_real_time_price(symbol, price, volume)
                check_price_alerts(symbol, price)
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    # Try to reconnect after a delay
    time.sleep(5)
    start_websocket([])

def on_open(ws):
    print("WebSocket connection opened")
    try:
        subscribe_message = {
            "type": "subscribe",
            "symbols": ["*"]  # Subscribe to all available symbols
        }
        ws.send(json.dumps(subscribe_message))
    except Exception as e:
        print(f"Error subscribing to updates: {e}")

def start_websocket(symbols):
    """Start WebSocket connection for real-time data"""
    try:
        ws = websocket.WebSocketApp(
            "wss://stream.data.alpaca.markets/v2/iex",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
    except Exception as e:
        print(f"Error starting WebSocket: {e}")

def is_valid_stock_symbol(symbol):
    """Validate stock symbol format"""
    if not symbol:
        return False
    # Basic validation for common stock symbol formats
    return bool(re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', symbol))

def get_stock_data(symbol, period='1y'):
    """Get stock data with error handling and validation"""
    if not is_valid_stock_symbol(symbol):
        return None, "Invalid stock symbol format"

    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        if hist.empty:
            return None, "No data available for this symbol"

        # Calculate technical indicators
        hist = calculate_technical_indicators(hist)

        # Get real-time data if available
        rt_data = get_real_time_price(symbol)
        if rt_data:
            current_time = datetime.now()
            hist.loc[current_time] = {
                'Open': rt_data['price'],
                'High': rt_data['price'],
                'Low': rt_data['price'],
                'Close': rt_data['price'],
                'Volume': rt_data['volume']
            }
            # Recalculate indicators with new data
            hist = calculate_technical_indicators(hist)

        return hist, None
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None, f"Error fetching data: {str(e)}"

def check_price_alerts(symbol, current_price):
    """Check and update price alerts in database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE price_alerts
            SET is_triggered = TRUE, triggered_at = CURRENT_TIMESTAMP
            WHERE symbol = %s AND 
                  NOT is_triggered AND
                  ((alert_type = 'above' AND %s > target_price) OR
                   (alert_type = 'below' AND %s < target_price))
            RETURNING id
        ''', (symbol, current_price, current_price))
        conn.commit()

def set_price_alert(user_id, symbol, price, alert_type='above'):
    """Set price alert in database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO price_alerts 
                (user_id, symbol, target_price, alert_type)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, symbol, price, alert_type))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error setting price alert: {e}")
            return False

def get_price_alerts(user_id, symbol):
    """Get price alerts from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT target_price, alert_type, is_triggered, triggered_at
            FROM price_alerts
            WHERE user_id = %s AND symbol = %s
            ORDER BY created_at DESC
        ''', (user_id, symbol))
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'price': float(row[0]),
                'type': row[1],
                'triggered': row[2],
                'trigger_time': row[3]
            })
        return alerts

def calculate_volume_profile(data):
    """Calculate volume profile analysis"""
    price_bins = np.linspace(data['Low'].min(), data['High'].max(), 20)
    volume_profile = np.zeros_like(price_bins)

    for i in range(len(price_bins)-1):
        mask = (data['Close'] >= price_bins[i]) & (data['Close'] < price_bins[i+1])
        volume_profile[i] = data.loc[mask, 'Volume'].sum()

    return price_bins, volume_profile

def calculate_technical_indicators(data):
    """Calculate comprehensive technical indicators"""
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # Moving Averages
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()

    # MACD
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD'] - data['Signal']

    # Bollinger Bands
    data['BB_middle'] = data['Close'].rolling(window=20).mean()
    data['BB_upper'] = data['BB_middle'] + 2 * data['Close'].rolling(window=20).std()
    data['BB_lower'] = data['BB_middle'] - 2 * data['Close'].rolling(window=20).std()

    # Stochastic Oscillator
    low_min = data['Low'].rolling(14).min()
    high_max = data['High'].rolling(14).max()
    data['%K'] = 100 * (data['Close'] - low_min) / (high_max - low_min)
    data['%D'] = data['%K'].rolling(3).mean()

    return data

def add_to_watchlist(user_id, symbol):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO watchlist (user_id, symbol)
                VALUES (%s, %s)
            ''', (user_id, symbol))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False

def get_watchlist(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT symbol FROM watchlist WHERE user_id = %s', (user_id,))
        return [row[0] for row in cursor.fetchall()]

def add_to_portfolio(user_id, symbol, shares, purchase_price):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO portfolio (user_id, symbol, shares, purchase_price)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, symbol, shares, purchase_price))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding to portfolio: {e}")
            return False

def get_portfolio(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, shares, purchase_price, purchase_date
            FROM portfolio WHERE user_id = %s
        ''', (user_id,))
        return cursor.fetchall()

def calculate_portfolio_metrics(portfolio_data):
    total_value = 0
    total_cost = 0
    portfolio_items = []

    for symbol, shares, purchase_price, purchase_date in portfolio_data:
        info = get_stock_info(symbol)
        if info:
            current_price = info['price']
            current_value = shares * current_price
            cost_basis = shares * purchase_price
            gain_loss = current_value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0

            total_value += current_value
            total_cost += cost_basis

            portfolio_items.append({
                'Symbol': symbol,
                'Shares': shares,
                'Purchase Price': f"${purchase_price:.2f}",
                'Current Price': f"${current_price:.2f}",
                'Total Value': f"${current_value:.2f}",
                'Gain/Loss': f"${gain_loss:.2f}",
                'Gain/Loss %': f"{gain_loss_pct:.2f}%"
            })

    portfolio_summary = {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_value - total_cost,
        'total_gain_loss_pct': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
    }

    return portfolio_items, portfolio_summary

def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        # Get real-time price if available
        rt_data = get_real_time_price(symbol)
        current_price = rt_data['price'] if rt_data else info.get('currentPrice', 0)

        return {
            'name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'price': current_price,
            'change': info.get('regularMarketChangePercent', 0),
            'volume': info.get('volume', 0),
            'avg_volume': info.get('averageVolume', 0),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'beta': info.get('beta', 'N/A'),
            '52w_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52w_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'description': info.get('longBusinessSummary', 'N/A')
        }
    except Exception as e:
        print(f"Error fetching stock info: {e}")
        return None

def render_technical_indicators(data):
    """Render comprehensive technical analysis visualization"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25]
    )

    # Price and Indicators
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='OHLC'
        ),
        row=1, col=1
    )

    # Add Stochastic
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['%K'],
            name='%K',
            line=dict(color='blue')
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['%D'],
            name='%D',
            line=dict(color='orange')
        ),
        row=2, col=1
    )

    # Add Volume
    colors = ['red' if row['Open'] - row['Close'] >= 0 
              else 'green' for index, row in data.iterrows()]
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors
        ),
        row=3, col=1
    )

    # Update layout
    fig.update_layout(
        title='Technical Analysis Dashboard',
        yaxis_title='Price',
        yaxis2_title='Stochastic',
        yaxis3_title='Volume',
        xaxis_rangeslider_visible=False,
        height=800
    )

    return fig

start_price_updates()