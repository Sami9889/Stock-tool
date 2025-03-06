import streamlit as st
import pandas as pd
from utils.stock_data import get_stock_data, get_key_metrics, calculate_technical_indicators
from utils.chart_utils import create_price_chart, create_rsi_chart
from utils.notifications import SystemNotification, StockAlertManager

# Copyright © 2025 Sami Singh. All rights reserved.

# Page config
st.set_page_config(
    page_title="Stock Analysis Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open('styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize notification system
if 'notification_manager' not in st.session_state:
    notification_provider = SystemNotification()
    st.session_state.notification_manager = StockAlertManager(notification_provider)

# Title and Description
st.title('📈 Stock Analysis Tool')
st.markdown("""
    Welcome to the Stock Analysis Tool - your comprehensive platform for financial market analysis.
    Enter a stock symbol below to view detailed charts and metrics.

    Developed by [Sami Singh](https://samiswebsite.tiiny.site/)
""")

# Sidebar
st.sidebar.header('Stock Selection')
symbol = st.sidebar.text_input('Enter Stock Symbol:', value='AAPL').upper()
period = st.sidebar.selectbox(
    'Select Time Period:',
    ('1mo', '3mo', '6mo', '1y', '2y', '5y')
)

# Alert Settings
st.sidebar.header('Price Alerts')
enable_alerts = st.sidebar.checkbox('Enable Price Alerts')
if enable_alerts:
    alert_threshold = st.sidebar.number_input(
        'Price Alert Threshold ($)',
        min_value=0.0,
        value=100.0,
        step=0.1
    )

# Main content
if symbol:
    with st.spinner(f'Loading data for {symbol}...'):
        hist_data, info = get_stock_data(symbol, period)

        if hist_data is not None and info is not None:
            # Company info
            st.subheader(f"{info.get('longName', symbol)} ({symbol})")

            # Current price for alerts
            current_price = hist_data['Close'].iloc[-1]

            # Check price alerts if enabled
            if enable_alerts and current_price > alert_threshold:
                if st.sidebar.button('Send Alert Now'):
                    # Show confirmation dialog
                    if st.sidebar.success("Click to confirm sending system notification"):
                        success = st.session_state.notification_manager.send_price_alert(
                            symbol=symbol,
                            current_price=current_price,
                            alert_type="above",
                            target_price=alert_threshold
                        )
                        if success:
                            st.sidebar.success("System notification sent!")
                        else:
                            st.sidebar.error("Failed to send notification")

            # Key metrics
            metrics = get_key_metrics(info)
            cols = st.columns(len(metrics))
            for col, (metric, value) in zip(cols, metrics.items()):
                col.metric(metric, value)

            # Calculate technical indicators
            df = calculate_technical_indicators(hist_data)

            # Charts
            st.subheader('Price Analysis')
            price_chart = create_price_chart(df)
            st.plotly_chart(price_chart, use_container_width=True)

            st.subheader('Technical Indicators')
            rsi_chart = create_rsi_chart(df)
            st.plotly_chart(rsi_chart, use_container_width=True)

            # Additional company information
            with st.expander("Company Information"):
                st.write(info.get('longBusinessSummary', 'No information available'))

        else:
            st.error(f"Unable to fetch data for {symbol}. Please check the symbol and try again.")

# Footer
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        Data provided by Yahoo Finance<br>
        © 2025 Sami Singh - Stock Analysis Tool<br>
        <a href="https://samiswebsite.tiiny.site/" target="_blank">Visit Developer's Website</a>
    </div>
    """, unsafe_allow_html=True)