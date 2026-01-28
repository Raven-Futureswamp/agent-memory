# Project: Automated Trading Systems

**Status:** 🟢 LIVE (all 3 systems)
**Created:** 2026-01-25
**Last Updated:** 2026-01-26

## Goal
Automated trading across crypto (Robinhood), stocks (Alpaca), and prediction markets (Kalshi) using AI-driven strategies with Grok as the primary sentiment/strategy advisor.

## Systems

### 1. Robinhood Crypto 🟢
- **Capital:** ~$5,260
- **Cron:** Every 4 hours
- **Code:** `trading/` (robinhood.js, grok.js, trader.js)
- **Strategy:** Grok sentiment-driven, $250 max/trade, $150 daily loss limit
- **Holdings:** BTC (long-term hold), DOGE (main), TRUMP, SOL, XRP, PEPE, BONK
- **Log:** `trading/log.md`

### 2. Alpaca Stocks 🟢
- **Capital:** $100
- **Cron:** Every 30 min during market hours
- **Code:** `scripts/trading/alpaca_trader.py`
- **Strategy:** Momentum + VWAP swing trading (Grok-optimized)
- **Watchlist:** NVDA, TSLA, AMD, META, PLTR, AAPL, MSFT + SPY, QQQ
- **Risk:** $45 max position, -2% stop loss, 2.5% trailing stop

### 3. Kalshi Prediction Markets 🟢
- **Capital:** $100
- **Cron:** Hourly
- **Code:** `scripts/kalshi/` (auto_trader.py, scanner.py, etc.)
- **Strategy:** Cross-platform arbitrage + CPI probability model
- **Data:** Kalshi, Polymarket, PredictIt, The Odds API, FRED
- **Risk:** $10 max per trade, max 6 positions

## Decisions Made
- (2026-01-26) BTC is a long-term hold — funnel profits there
- (2026-01-26) Grok is the primary strategy advisor for all systems
- (2026-01-26) Jess said "do what you think is best" — full autonomy on trades within risk limits
- (2026-01-26) Trimmed 25% DOGE, diversified into BTC/SOL/TRUMP

## Key Lessons
- Kalshi Python SDK v2.1.4 uses kwargs for orders, not CreateOrderRequest objects
- Fuzzy matching across platforms creates garbage — strict keyword matching only
- Always log trades to trading/log.md

## API Keys
All in `.env` — see TOOLS.md for full list
