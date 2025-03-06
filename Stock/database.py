import os
import psycopg2
from contextlib import contextmanager
from datetime import datetime

@contextmanager
def get_db_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(
        dbname=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD'),
        host=os.getenv('PGHOST'),
        port=os.getenv('PGPORT')
    )
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create watchlist table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            symbol VARCHAR(10) NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol)
        )
        ''')

        # Create portfolio table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            symbol VARCHAR(10) NOT NULL,
            shares DECIMAL(10,2) NOT NULL,
            purchase_price DECIMAL(10,2) NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create price_alerts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            symbol VARCHAR(10) NOT NULL,
            target_price DECIMAL(10,2) NOT NULL,
            alert_type VARCHAR(10) NOT NULL CHECK (alert_type IN ('above', 'below')),
            is_triggered BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            triggered_at TIMESTAMP
        )
        ''')

        # Create historical_prices table for caching
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_prices (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            date TIMESTAMP NOT NULL,
            open_price DECIMAL(10,2) NOT NULL,
            high_price DECIMAL(10,2) NOT NULL,
            low_price DECIMAL(10,2) NOT NULL,
            close_price DECIMAL(10,2) NOT NULL,
            volume BIGINT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
        ''')

        # Create real_time_prices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS real_time_prices (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            volume BIGINT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol)
        )
        ''')

        conn.commit()