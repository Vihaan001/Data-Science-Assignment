import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="PrimeTrade Sentiment Analysis", layout="wide")

st.title("📈 PrimeTrade: Trader Performance vs Market Sentiment")
st.markdown("Analyze how Bitcoin's Fear & Greed Index correlates with trader activities on Hyperliquid.")

# Caching Data to dramatically improve Streamlit refresh times
@st.cache_data
def load_data():
    st.write("Processing Datasets... Please wait.")
    df_fg = pd.read_csv('fear_greed_index.csv')
    df_hd = pd.read_csv('historical_data.csv')

    df_fg['date'] = pd.to_datetime(df_fg['date'])
    df_hd['Timestamp IST'] = pd.to_datetime(df_hd['Timestamp IST'], format='%d-%m-%Y %H:%M', errors='coerce')
    df_hd = df_hd.dropna(subset=['Timestamp IST']).copy()
    df_hd['date'] = pd.to_datetime(df_hd['Timestamp IST'].dt.date)

    df = pd.merge(df_hd, df_fg[['date', 'value', 'classification']], on='date', how='left')
    df = df.dropna(subset=['classification']).copy()

    df['Closed PnL'] = pd.to_numeric(df['Closed PnL'], errors='coerce').fillna(0)
    df['Size USD'] = pd.to_numeric(df['Size USD'], errors='coerce').fillna(0)
    df['Fee'] = pd.to_numeric(df['Fee'], errors='coerce').fillna(0)
    df['Net PnL'] = df['Closed PnL'] - df['Fee']

    def map_sentiment(x):
        if 'Fear' in x: return 'Fear'
        elif 'Greed' in x: return 'Greed'
        else: return 'Neutral'

    df['Sentiment'] = df['classification'].apply(map_sentiment)

    daily = df.groupby(['Account', 'date']).agg(
        daily_qty_trades=('Trade ID', 'count'),
        daily_pnl=('Net PnL', 'sum'),
        avg_trade_size=('Size USD', 'mean'),
        win_trades=('Net PnL', lambda x: (x > 0).sum()),
        loss_trades=('Net PnL', lambda x: (x < 0).sum()),
        long_trades=('Direction', lambda x: (x == 'Buy').sum()),
        short_trades=('Direction', lambda x: (x == 'Sell').sum())
    ).reset_index()

    daily['win_rate'] = daily['win_trades'] / (daily['win_trades'] + daily['loss_trades']).replace(0, 1)
    daily['long_short_ratio'] = daily['long_trades'] / daily['short_trades'].replace(0, 1)

    daily = pd.merge(daily, df_fg[['date', 'classification', 'value']], on='date', how='left')
    daily['Sentiment'] = daily['classification'].apply(map_sentiment)
    
    return df, daily

try:
    raw_df, daily_metrics = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.sidebar.header("Filter Results")
selected_sentiment = st.sidebar.multiselect(
    "Market Sentiment:",
    options=daily_metrics['Sentiment'].unique(),
    default=daily_metrics['Sentiment'].unique()
)

min_trades = st.sidebar.slider("Min Daily Trades by Account", min_value=1, max_value=500, value=1)

filtered = daily_metrics[(daily_metrics['Sentiment'].isin(selected_sentiment)) & (daily_metrics['daily_qty_trades'] >= min_trades)]

st.subheader("High-Level Core Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Average Daily PnL", f"${filtered['daily_pnl'].mean():,.2f}")
col2.metric("Average Trade Size", f"${filtered['avg_trade_size'].mean():,.2f}")
col3.metric("Average Win Rate", f"{filtered['win_rate'].mean()*100:.1f}%")

st.markdown("---")

st.subheader("Performance & Behavior Distributions")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(data=filtered, x='Sentiment', y='daily_pnl', ax=axes[0], showfliers=False)
axes[0].set_title('Daily PnL Distribution by Sentiment')
axes[0].set_ylabel('Net PnL (USD)')

sns.barplot(data=filtered, x='Sentiment', y='avg_trade_size', ax=axes[1], errorbar=None)
axes[1].set_title('Avg Account Trade Size by Sentiment')
axes[1].set_ylabel('Size USD')

st.pyplot(fig)

st.markdown("---")
st.subheader("Historical Filtered Data Preview")
st.dataframe(filtered.head(50))
