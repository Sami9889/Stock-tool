import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import time
from database import init_db
from auth import init_session_state, login_user, register_user
from stock_utils import (
    get_stock_data, get_stock_info, add_to_watchlist,
    get_watchlist, add_to_portfolio, get_portfolio,
    calculate_portfolio_metrics, start_price_updates, calculate_volume_profile,
    set_price_alert, get_price_alerts, render_technical_indicators, is_valid_stock_symbol
)

# Initialize database and session state
init_db()
init_session_state()

# Start background price updates
start_price_updates()

# Apply custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Add auto-refresh to session state
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

def render_login_page():
    st.title("StockSentinel - Login")

    col1, col2 = st.columns([2, 1])
    with col1:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")

                if submit:
                    if username and password:
                        user_id = login_user(username, password)
                        if user_id:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Please fill in all fields")

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                # Password requirements helper
                st.markdown("""
                Password must contain:
                - At least 8 characters
                - At least one uppercase letter
                - At least one lowercase letter
                - At least one number
                """)

                submit = st.form_submit_button("Register")

                if submit:
                    if not new_username or not new_password or not confirm_password:
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords don't match")
                    elif register_user(new_username, new_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists or invalid input")

    with col2:
        st.image("https://img.icons8.com/color/96/000000/stocks.png", width=100)
        st.markdown("""
        ### Welcome to StockSentinel
        Your trusted companion for stock market analysis and portfolio management.
        """)

def render_stock_chart(symbol, data):
    if data is not None:
        # Create main chart with candlesticks and indicators
        fig = go.Figure()

        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='OHLC'
        ))

        # Add Bollinger Bands
        if 'BB_middle' in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index, y=data['BB_middle'],
                name='BB Middle', line=dict(color='gray', width=1)
            ))
            fig.add_trace(go.Scatter(
                x=data.index, y=data['BB_upper'],
                name='BB Upper', line=dict(color='gray', dash='dash', width=1)
            ))
            fig.add_trace(go.Scatter(
                x=data.index, y=data['BB_lower'],
                name='BB Lower', line=dict(color='gray', dash='dash', width=1),
                fill='tonexty'
            ))

        # Add Moving Averages
        for ma in ['SMA_20', 'SMA_50', 'SMA_200']:
            if ma in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data[ma],
                    name=ma, line=dict(width=1)
                ))

        fig.update_layout(
            title=f'{symbol} Stock Price',
            yaxis_title='Price',
            template='plotly_white',
            height=600,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Technical Indicators in separate charts
        col1, col2 = st.columns(2)

        with col1:
            # RSI Chart
            if 'RSI' in data.columns:
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=data.index, y=data['RSI'],
                    name='RSI'
                ))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                fig_rsi.update_layout(
                    title='Relative Strength Index (RSI)',
                    yaxis_title='RSI',
                    template='plotly_white',
                    height=300
                )
                st.plotly_chart(fig_rsi, use_container_width=True)

        with col2:
            # MACD Chart
            if all(x in data.columns for x in ['MACD', 'Signal', 'MACD_Histogram']):
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(
                    x=data.index, y=data['MACD'],
                    name='MACD'
                ))
                fig_macd.add_trace(go.Scatter(
                    x=data.index, y=data['Signal'],
                    name='Signal'
                ))
                fig_macd.add_trace(go.Bar(
                    x=data.index, y=data['MACD_Histogram'],
                    name='Histogram'
                ))
                fig_macd.update_layout(
                    title='MACD',
                    template='plotly_white',
                    height=300
                )
                st.plotly_chart(fig_macd, use_container_width=True)

def render_stock_details(symbol, info):
    """Render detailed stock information with error handling"""
    if not info:
        st.error("Unable to fetch stock information")
        return

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(f"### {info['name']} ({symbol})")
        st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
        st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
        price_color = "positive-change" if info.get('change', 0) > 0 else "negative-change"
        st.markdown(f"**Price:** ${info.get('price', 0):.2f} <span class='{price_color}'>({info.get('change', 0):.2f}%)</span>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**P/E Ratio:** {info.get('pe_ratio', 'N/A')}")
        st.markdown(f"**Forward P/E:** {info.get('forward_pe', 'N/A')}")
        st.markdown(f"**Dividend Yield:** {info.get('dividend_yield', 'N/A')}")
        st.markdown(f"**Beta:** {info.get('beta', 'N/A')}")

    with col3:
        st.markdown(f"**52W High:** ${info.get('52w_high', 'N/A')}")
        st.markdown(f"**52W Low:** ${info.get('52w_low', 'N/A')}")
        st.markdown(f"**Volume:** {info.get('volume', 0):,}")
        st.markdown(f"**Avg Volume:** {info.get('avg_volume', 0):,}")

    with st.expander("Company Description"):
        st.write(info.get('description', 'No description available'))

def render_volume_profile(data):
    """Render volume profile analysis"""
    price_bins, volume_profile = calculate_volume_profile(data)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=volume_profile,
        y=price_bins[:-1],
        orientation='h',
        name='Volume Profile'
    ))

    fig.update_layout(
        title='Volume Profile Analysis',
        xaxis_title='Volume',
        yaxis_title='Price',
        template='plotly_white',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def render_price_alerts(symbol):
    """Render price alerts section"""
    st.subheader("Price Alerts")

    col1, col2 = st.columns([3, 1])
    with col1:
        alert_price = st.number_input("Alert Price", min_value=0.01, step=0.01)
    with col2:
        alert_type = st.selectbox("Alert Type", ["above", "below"])

    if st.button("Set Alert"):
        if set_price_alert(st.session_state.user_id, symbol, alert_price, alert_type):
            st.success(f"Alert set for {symbol} at ${alert_price} ({alert_type})")
        else:
            st.error("Failed to set price alert")

    # Display existing alerts
    alerts = get_price_alerts(st.session_state.user_id, symbol)
    if alerts:
        st.write("Active Alerts:")
        for alert in alerts:
            status = "🔔 Triggered" if alert['triggered'] else "⏳ Waiting"
            st.write(f"{status} - ${alert['price']} ({alert['type']})")

def render_portfolio_performance(portfolio_data):
    """Render portfolio performance charts"""
    if not portfolio_data:
        return

    portfolio_items, summary = calculate_portfolio_metrics(portfolio_data)

    # Portfolio Composition Pie Chart
    portfolio_df = pd.DataFrame(portfolio_items)
    fig_composition = go.Figure(data=[go.Pie(
        labels=portfolio_df['Symbol'],
        values=portfolio_df['Total Value'].str.replace('$', '').str.replace(',', '').astype(float),
        hole=.3
    )])
    fig_composition.update_layout(title='Portfolio Composition')
    st.plotly_chart(fig_composition, use_container_width=True)

    # Performance Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Value",
            f"${summary['total_value']:,.2f}",
            f"{summary['total_gain_loss_pct']:.1f}%"
        )
    with col2:
        st.metric(
            "Total Gain/Loss",
            f"${summary['total_gain_loss']:,.2f}"
        )
    with col3:
        st.metric(
            "Number of Stocks",
            len(portfolio_items)
        )


def render_main_page():
    st.title(f"Welcome to StockSentinel, {st.session_state.username}!")

    # Auto-refresh toggle
    st.sidebar.toggle("Auto-refresh data", key="auto_refresh")

    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Search", "Watchlist", "Portfolio"])

    if page == "Search":
        st.subheader("Search Stocks")
        col1, col2 = st.columns([3, 1])

        with col1:
            symbol = st.text_input("Enter Stock Symbol (e.g., AAPL)").upper()
            if symbol and not is_valid_stock_symbol(symbol):
                st.error("Invalid stock symbol format. Please enter a valid symbol (e.g., AAPL, MSFT)")
                return

        with col2:
            period = st.selectbox(
                "Time Period",
                ['1mo', '3mo', '6mo', '1y', '2y', '5y'],
                index=3
            )

        if symbol and is_valid_stock_symbol(symbol):
            with st.spinner('Fetching stock data...'):
                info = get_stock_info(symbol)
                if info:
                    # Stock Details
                    render_stock_details(symbol, info)

                    # Price Alerts
                    render_price_alerts(symbol)

                    # Charts
                    data, error_msg = get_stock_data(symbol, period=period)
                    if error_msg:
                        st.error(error_msg)
                    elif data is not None:
                        tab1, tab2, tab3 = st.tabs([
                            "Price & Indicators",
                            "Volume Analysis",
                            "Technical Analysis"
                        ])

                        with tab1:
                            render_stock_chart(symbol, data)

                        with tab2:
                            render_volume_profile(data)

                        with tab3:
                            st.plotly_chart(
                                render_technical_indicators(data),
                                use_container_width=True
                            )

                    # Trading Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Add to Watchlist"):
                            if add_to_watchlist(st.session_state.user_id, symbol):
                                st.success(f"Added {symbol} to watchlist")
                            else:
                                st.error("Failed to add to watchlist")

                    with col2:
                        shares = st.number_input("Shares", min_value=0.01, step=0.01)
                        if st.button("Add to Portfolio"):
                            if add_to_portfolio(
                                st.session_state.user_id,
                                symbol,
                                shares,
                                info['price']
                            ):
                                st.success(f"Added {shares} shares of {symbol} to portfolio")
                            else:
                                st.error("Failed to add to portfolio")
                else:
                    st.error("Unable to fetch stock information. Please verify the symbol and try again.")

    elif page == "Watchlist":
        st.subheader("Your Watchlist")
        watchlist = get_watchlist(st.session_state.user_id)

        if watchlist:
            cols = st.columns(2)
            for idx, symbol in enumerate(watchlist):
                with cols[idx % 2]:
                    info = get_stock_info(symbol)
                    if info:
                        with st.container():
                            st.markdown(f"### {info['name']} ({symbol})")
                            price_color = "positive-change" if info['change'] > 0 else "negative-change"
                            st.markdown(f"**Price:** ${info['price']:.2f} <span class='{price_color}'>({info['change']:.2f}%)</span>", unsafe_allow_html=True)
                            st.markdown(f"**Volume:** {info['volume']:,}")
        else:
            st.info("Your watchlist is empty")

    elif page == "Portfolio":
        st.subheader("Your Portfolio")
        portfolio = get_portfolio(st.session_state.user_id)

        if portfolio:
            render_portfolio_performance(portfolio)
        else:
            st.info("Your portfolio is empty")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

def main():
    if not st.session_state.logged_in:
        render_login_page()
    else:
        render_main_page()
        # Auto-refresh every 5 seconds if enabled
        if st.session_state.auto_refresh:
            time.sleep(5)
            st.rerun()

if __name__ == "__main__":
    main()