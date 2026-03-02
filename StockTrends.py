import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine
import streamlit as st

# Collect
@st.cache_data
def collect_data(tickers, lookback):
    data = []
    for ticker in tickers:
        df = yf.download(ticker, period=lookback, interval="1h") 
        df.reset_index(inplace=True)
        df["ticker"] = ticker 
        data.append(df)
    combined = pd.concat(data, ignore_index=True)
    return combined

# Clean
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
    df["ticker"] = df["ticker"].str.replace("_Close", "", regex=False)
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    df["Close"] = df["Close"].interpolate()
    df["Daily_Return"] = df.groupby("ticker")["Close"].pct_change()

    # Relative Strength Index
    def compute_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    df["RSI"] = df.groupby("ticker")["Close"].transform(lambda x: compute_rsi(x))
    df["SMA_20"] = df.groupby("ticker")["Close"].transform(lambda x: x.rolling(window=20).mean())

    return df

# Storage
def save_db(df, table_name="clean_data", db_url="sqlite:///stock_data.db"):
    engine = create_engine(db_url)
    df.to_sql(table_name, con=engine, if_exists="replace", index=False) 

def read_db(table_name="clean_data", db_url="sqlite:///stock_data.db"):
    engine = create_engine(db_url)
    try:
        return pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
    except:
        return pd.DataFrame() # Returns empty dataframe if table doesn't exist yet

# Dashboard
def run_dashboard():
    st.set_page_config(page_title="AlphaStream Insights", layout="wide")
    st.title("Financial Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")

        lookback = st.selectbox("Select Lookback Period", ["7d", "14d", "28d"], index=2)
        
        if "ticker_list" not in st.session_state:
            st.session_state.ticker_list = []
        new_ticker = st.text_input("Add a Ticker").upper().strip()
        
        if st.button("Add to List"):
            if new_ticker:
                if new_ticker not in st.session_state.ticker_list:
                    st.session_state.ticker_list.append(new_ticker)
                    st.success(f"Added {new_ticker}")
                else:
                    st.info(f"{new_ticker} is already in the list.")
            else:
                st.error("Please enter a ticker symbol.")

        if st.session_state.ticker_list:
            tickers = st.multiselect(
                "Select Tickers to Fetch", 
                options=st.session_state.ticker_list, 
                default=st.session_state.ticker_list
            )
            
            if st.button("Fetch New Data"):
                with st.spinner("Updating Database..."):
                    raw_df = collect_data(tickers, lookback)
                    if not raw_df.empty:
                        clean_df = clean_data(raw_df)
                        save_db(clean_df)
                        st.success("Database Updated!")
                    else:
                        st.error("No data found for selected tickers.")

            if st.button("Clear Ticker List"):
                st.session_state.ticker_list = []
                st.rerun()
        else:
            st.info("Your ticker list is empty. Add a symbol above to get started!")

    # Layout
    df = read_db()
    if not df.empty:
        selected_ticker = st.selectbox("View Analysis For:", df["ticker"].unique())
        filtered = df[df["ticker"] == selected_ticker]

        col1, col2, col3 = st.columns(3)
        current_price = filtered["Close"].iloc[-1]
        delta = filtered["Daily_Return"].iloc[-1]
        
        col1.metric("Current Price", f"${current_price:.2f}", f"{delta:.2%}")
        col2.metric("RSI (14)", f"{filtered['RSI'].iloc[-1]:.2f}")
        col3.metric(f"{lookback.upper()} High", f"${filtered['Close'].max():.2f}")

        st.line_chart(filtered, x="Datetime", y=["Close", "SMA_20"])
    else:
        st.warning("No data in the database. Please add a ticker and fetch data from the sidebar.")

if __name__ == "__main__":
    run_dashboard()