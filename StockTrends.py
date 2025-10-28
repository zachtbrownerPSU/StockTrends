import pandas as pd
import yfinance as yf #Yahoo Finance API
from sqlalchemy import create_engine
import streamlit as st

#Collect
@st.cache_data #Tell streamlit to remember the result of the function the first time it is ran so it doesn't have to rerun
def collect_data(tickers):
    data = []
    for ticker in tickers:
        df = yf.download(ticker, period = "7d", interval = "1h") #Downloads hourly data for the last 7 days
        df.reset_index(inplace = True) #Resets index to turn Datetime into a column
        df["ticker"] = ticker 
        data.append(df)
    combined = pd.concat(data, ignore_index=True) #Combines data for all tickers into one data frame
    return combined

#Clean
def clean_data(df):
    df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]
    df = df.melt(
        id_vars="Datetime", 
        value_vars=[c for c in df.columns if "Close" in c],
        var_name="ticker",
        value_name="Close"
    )
    df["ticker"] = df["ticker"].str.replace("_Close", "", regex=False) # Clean ticker names
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    df["Close"] = df["Close"].interpolate() # Interpolate missing Close values
    df["Daily_Return"] = df.groupby("ticker")["Close"].pct_change() # Compute daily returns per ticker
    return df

#Storage
def save_db(df, table_name = "clean_data", db_url = "sqlite:///stock_data.db"):
    engine = create_engine(db_url)
    df.to_sql(table_name, con = engine, if_exists = "replace", index = False)

def read_db(table_name = "clean_data", db_url = "sqlite:///stock_data.db"):
    engine = create_engine(db_url)
    return pd.read_sql(f"SELECT * FROM {table_name}", con=engine)

#Dashboard
def run_dashboard():
    st.title("Stock Data Dashboard")
    tickers = ["AAPL", "MSFT", "GOOGL"]
    raw_df = collect_data(tickers) #Collect
    clean_df = clean_data(raw_df) #Clean
    save_db(clean_df) #Store
    df = read_db() #Read
    ticker = st.selectbox("Select Ticker", df["ticker"].unique()) #User chooses what ticker to view
    filtered = df[df["ticker"] == ticker]
    st.subheader("Stock Prices (Last 7 Days)")
    st.line_chart(filtered, x = "Datetime", y = "Close")
    st.subheader("Daily Returns")
    st.bar_chart(filtered, x = "Datetime", y = "Daily_Return")
    st.subheader("Data Preview")
    st.dataframe(filtered.tail(10))

if __name__ == "__main__":
    run_dashboard()