import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('charts', exist_ok=True)

# 1. Load Data
df_fg = pd.read_csv('fear_greed_index.csv')
df_hd = pd.read_csv('historical_data.csv')

print("--- Data Info ---")
print(f"Fear & Greed Index: {df_fg.shape[0]} rows, {df_fg.shape[1]} cols")
print(f"Historical Data: {df_hd.shape[0]} rows, {df_hd.shape[1]} cols")
print(f"Historical Data Missing Values:\n{df_hd.isna().sum()}")
print(f"Historical Data Duplicates: {df_hd.duplicated().sum()}")

# 2. Convert Timestamps and Align Datasets
df_fg['date'] = pd.to_datetime(df_fg['date'])

# Historical data 'Timestamp IST' format: '02-12-2024 22:50'
# Convert to datetime and then to date
df_hd['Timestamp IST'] = pd.to_datetime(df_hd['Timestamp IST'], format='%d-%m-%Y %H:%M', errors='coerce')
df_hd = df_hd.dropna(subset=['Timestamp IST']).copy()
df_hd['date'] = df_hd['Timestamp IST'].dt.date
df_hd['date'] = pd.to_datetime(df_hd['date'])

# Merge historical data with fear/greed classifications
df = pd.merge(df_hd, df_fg[['date', 'value', 'classification']], on='date', how='left')

# Drop rows where classification is NaN (if any dates don't align)
df = df.dropna(subset=['classification']).copy()

# Ensure types
df['Closed PnL'] = pd.to_numeric(df['Closed PnL'], errors='coerce').fillna(0)
df['Size USD'] = pd.to_numeric(df['Size USD'], errors='coerce').fillna(0)
df['Fee'] = pd.to_numeric(df['Fee'], errors='coerce').fillna(0)

# Net PnL = Closed PnL - Fee
df['Net PnL'] = df['Closed PnL'] - df['Fee']

# Combine Fear/Extreme Fear and Greed/Extreme Greed for simplicity
def map_sentiment(x):
    if 'Fear' in x: return 'Fear'
    elif 'Greed' in x: return 'Greed'
    else: return 'Neutral'

df['Sentiment'] = df['classification'].apply(map_sentiment)

# --- Part A Key Metrics Creation ---
# Let's aggregate daily metrics per trader
daily_trader_metrics = df.groupby(['Account', 'date']).agg(
    daily_qty_trades=('Trade ID', 'count'),
    daily_pnl=('Net PnL', 'sum'),
    avg_trade_size=('Size USD', 'mean'),
    win_trades=('Net PnL', lambda x: (x > 0).sum()),
    loss_trades=('Net PnL', lambda x: (x < 0).sum()),
    long_trades=('Direction', lambda x: (x == 'Buy').sum()),
    short_trades=('Direction', lambda x: (x == 'Sell').sum())
).reset_index()

daily_trader_metrics['win_rate'] = daily_trader_metrics['win_trades'] / (daily_trader_metrics['win_trades'] + daily_trader_metrics['loss_trades'])
daily_trader_metrics['win_rate'] = daily_trader_metrics['win_rate'].fillna(0)
daily_trader_metrics['long_short_ratio'] = daily_trader_metrics['long_trades'] / daily_trader_metrics['short_trades'].replace(0, 1)

# Add Sentiment to daily trader metrics
daily_trader_metrics = pd.merge(daily_trader_metrics, df_fg[['date', 'classification', 'value']], on='date', how='left')
daily_trader_metrics['Sentiment'] = daily_trader_metrics['classification'].apply(map_sentiment)

print(f"\nCreated Daily Trader Metrics mapping: {daily_trader_metrics.shape[0]} rows.")

# --- Part B Analysis ---
# Q1: Does performance differ between Fear vs Greed days?
print("\n--- Performance by Sentiment ---")
perf_by_sent = daily_trader_metrics.groupby('Sentiment').agg(
    avg_daily_pnl=('daily_pnl', 'mean'),
    avg_win_rate=('win_rate', 'mean'),
    mean_trades_per_day=('daily_qty_trades', 'mean'),
    total_days=('date', 'nunique')
).reset_index()
print(perf_by_sent)

plt.figure(figsize=(8,5))
sns.barplot(data=perf_by_sent, x='Sentiment', y='avg_daily_pnl')
plt.title('Average Daily PnL per Trader by Sentiment')
plt.ylabel('Average Daily PnL (USD)')
plt.savefig('charts/avg_daily_pnl_by_sentiment.png')

plt.figure(figsize=(8,5))
sns.barplot(data=perf_by_sent, x='Sentiment', y='avg_win_rate')
plt.title('Average Win Rate per Trader by Sentiment')
plt.ylabel('Win Rate')
plt.savefig('charts/avg_win_rate_by_sentiment.png')

# Q2: Do traders change behavior based on sentiment?
print("\n--- Behavior by Sentiment ---")
behav_by_sent = daily_trader_metrics.groupby('Sentiment').agg(
    avg_trade_size=('avg_trade_size', 'mean'),
    avg_trades_freq=('daily_qty_trades', 'mean'),
    avg_long_short_ratio=('long_short_ratio', 'mean')
).reset_index()
print(behav_by_sent)

plt.figure(figsize=(8,5))
sns.barplot(data=behav_by_sent, x='Sentiment', y='avg_trade_size')
plt.title('Average Trade Size by Sentiment')
plt.ylabel('Avg Trade Size (USD)')
plt.savefig('charts/avg_trade_size_by_sentiment.png')

plt.figure(figsize=(8,5))
sns.barplot(data=behav_by_sent, x='Sentiment', y='avg_trades_freq')
plt.title('Average Trade Frequency (Trades/Day) by Sentiment')
plt.ylabel('Avg Trades per Day')
plt.savefig('charts/avg_trade_freq_by_sentiment.png')

# Segments
# Frequent vs Infrequent
# Calculate overall frequency per trader
trader_stats = daily_trader_metrics.groupby('Account').agg(
    total_trades=('daily_qty_trades', 'sum'),
    active_days=('date', 'nunique'),
    total_pnl=('daily_pnl', 'sum'),
    avg_pnl=('daily_pnl', 'mean'),
    win_rate=('win_rate', 'mean'),
    avg_trade_size=('avg_trade_size', 'mean')
).reset_index()
trader_stats['trades_per_day'] = trader_stats['total_trades'] / trader_stats['active_days']

freq_median = trader_stats['trades_per_day'].median()
trader_stats['Freq_Segment'] = np.where(trader_stats['trades_per_day'] > freq_median, 'Frequent', 'Infrequent')

# PnL Segment
pnl_median = trader_stats['total_pnl'].median()
trader_stats['PnL_Segment'] = np.where(trader_stats['total_pnl'] > 0, 'Profitable', 'Losing')

# Analyze Frequent vs Infrequent on Sentiments
seg_daily = pd.merge(daily_trader_metrics, trader_stats[['Account', 'Freq_Segment', 'PnL_Segment']], on='Account')

print("\n--- Freq_Segment Performance by Sentiment ---")
freq_sent = seg_daily.groupby(['Freq_Segment', 'Sentiment'])['daily_pnl'].mean().unstack()
print(freq_sent)

plt.figure(figsize=(10,6))
freq_sent.plot(kind='bar', figsize=(10,6))
plt.title('Daily PnL by Trader Frequency Segment & Sentiment')
plt.ylabel('Average Daily PnL (USD)')
plt.xticks(rotation=0)
plt.savefig('charts/pnl_freq_segment_sentiment.png')

print("\n--- PnL_Segment Behavior by Sentiment ---")
pvl_sent = seg_daily.groupby(['PnL_Segment', 'Sentiment'])['avg_trade_size'].mean().unstack()
print(pvl_sent)

plt.figure(figsize=(10,6))
pvl_sent.plot(kind='bar', figsize=(10,6))
plt.title('Average Trade Size by Trailing Profitability & Sentiment')
plt.ylabel('Average Trade Size (USD)')
plt.xticks(rotation=0)
plt.savefig('charts/trade_size_pnl_segment_sentiment.png')

# Bonus: Simple Predictive Model
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Predict if next day is profitable (1) or losing (0) for a trader based on current day features + sentiment
seg_daily_sorted = seg_daily.sort_values(by=['Account', 'date']).reset_index(drop=True)
seg_daily_sorted['next_day_pnl'] = seg_daily_sorted.groupby('Account')['daily_pnl'].shift(-1)
model_df = seg_daily_sorted.dropna(subset=['next_day_pnl']).copy()
model_df['target'] = (model_df['next_day_pnl'] > 0).astype(int)

# Features: current day daily_qty_trades, avg_trade_size, win_rate, value (fear greed index score)
features = ['daily_qty_trades', 'avg_trade_size', 'win_rate', 'value']
X = model_df[features]
y = model_df['target']

if len(model_df) > 50:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    preds = rf.predict(X_test)
    print("\n--- Predictive Model (Predicting Next Day Profitability) ---")
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print(classification_report(y_test, preds))

    importances = rf.feature_importances_
    for f, i in zip(features, importances):
        print(f"Feature: {f:<20} Importance: {i:.4f}")
else:
    print("\nNot enough data for the predictive model.")
