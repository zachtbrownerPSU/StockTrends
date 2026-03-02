# Financial Data Pipeline
A data engineering project that fetches, processes, and visualizes real-time stock market metrics using a custom-built analytics engine.

## The Tech Stack
* Language: Python
* Data Processing: Pandas
* API: Yahoo Finance (yfinance)
* Storage: SQLite & SQLAlchemy
* Dashboard: Streamlit

## How it Works
1. Extract: Pulls 28-day hourly market data from the Yahoo Finance API
2. Transform: Cleans and reshapes data using Pandas. Calculates RSI and 20-period SMAs.
3. Load: Persists cleaned records into a local SQLite database using SQLAlchemy.

## Technical Indicators
* Relative Strength Index (RSI): Calculated using Wilder's Smoothing Method to identify overbought/oversold conditions.
  $$RSI = 100 - \left( \frac{100}{1 + \frac{\text{Average Gain}}{\text{Average Loss}}} \right)$$
* Simple Moving Average (SMA-20): Used to identify short-term price trends.
