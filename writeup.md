# PrimeTrade Assignment: Methodology & Insights Write-up

## Methodology
The assignment integrates the Bitcoin Fear/Greed Index with a granular history of trader executions on the Hyperliquid exchange. 

1. **Data Preparation**: 
   - I extracted daily timestamps by reconciling Hyperliquid's IST execution timestamps with the Fear/Greed classification dates.
   - Using the mapped dates, I synthesized key daily metrics per individual trading account: *Daily PnL (Net of Fees), Average Trade Size (USD proxy for leverage due to missing metadata), Trade Frequency, Win Rate, and Long/Short bias*.
2. **Behavioral Segmentation**: 
   - Traders were clustered into binary cohorts: **Frequent vs Infrequent** (based on median trades/day) and **Profitable vs Losing** (Trailing performance threshold = 0 PnL).
3. **Cross-analysis**: 
   - These trader cohorts were then intersected with current market sentiment—quantifying variations in behavior and financial success given external conditions.

*(Note: "Leverage" was not available in the data dump. We substituted average Position Size USD to approximate exposure dynamics.)*

## Key Insights
- **Insight 1: "Fear" is the Catalyst for Maximum Activity & Size:** 
  Traders execute more frequently (Avg: 105 trades/day) with much larger trade sizes (~$8,500) during Fear than on Greed days (76.9 trades/day at ~$5,950). Extreme negative sentiment breeds systemic volatility which prompts traders to size up and interact aggressively with the market.
- **Insight 2: Divergent Cohort Performance — Frequency Matters:** 
  The "Frequent" trader cohort achieved substantially better capital returns during Fear days (~$7,700 average daily PnL) compared to Greed days (~$4,843). By contrast, "Infrequent" (typically trend-following) traders saw drastically reduced performance on Fear days compared to Greed days.
- **Insight 3: The Danger of "Revenge Trading" on Losing Accounts:** 
  Historically "Losing" traders massively ballooned their average trade size during Fear cycles ($10,740 vs $3,217 on Greed). Profitable traders showed much lower sizing elasticity. This indicates that losers employ revenge trading/improper risk management during downside volatility.

## Strategy Recommendations (Rules of Thumb)
Based on empirical findings, we can define two rules for portfolio managers or algorithmic strategies on Hyperliquid:

1. **Conditional Risk Tiers for Retail Users during Panic:** Implement dynamic maximum-position caps for empirically "Losing" accounts strictly during successive "Fear" market conditions. Protecting these accounts from ballooning leverage prevents systemic portfolio liquidations due to revenge trading.
2. **Market-Regime Execution Rotation:** Rotate overarching strategy allocation based on sentiment class. Allocate capital to **high-frequency scalping/mean-reversion** strategies precisely when the market flashes "Fear/Extreme Fear", as daily yields nearly double. For "Greed" markets where momentum is stable but volume is low, deploy **low-frequency trend-following** architectures. 
