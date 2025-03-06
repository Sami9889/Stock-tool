# Copyright © 2025 Sami Singh. All rights reserved.

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_price_chart(df):
    """
    Create an interactive price chart with technical indicators
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.7, 0.3])

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC'
    ), row=1, col=1)

    # Add SMAs
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA20'],
        name='SMA20',
        line=dict(color='orange', width=1)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA50'],
        name='SMA50',
        line=dict(color='blue', width=1)
    ), row=1, col=1)

    # Volume bars
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color='rgba(100,100,255,0.5)'
    ), row=2, col=1)

    # Update layout
    fig.update_layout(
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        title_text='Stock Price & Volume',
        yaxis_title='Price',
        yaxis2_title='Volume'
    )

    return fig

def create_rsi_chart(df):
    """
    Create RSI chart
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['RSI'],
        name='RSI',
        line=dict(color='purple', width=1)
    ))

    # Add RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5)

    fig.update_layout(
        template='plotly_dark',
        height=400,
        title_text='Relative Strength Index (RSI)',
        yaxis_title='RSI',
        yaxis=dict(range=[0, 100])
    )

    return fig