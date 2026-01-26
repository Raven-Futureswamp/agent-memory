# Alpaca Stock Trading 📈

*Automated stock trading system for Alpaca*

Started: 2025-06-28
Platform: Alpaca (LIVE account, not paper)
Capital: $100

**Status:** ✅ ACTIVE — Level 2 Auto-Trader live
**Auto-Trader:** `scripts/trading/alpaca_trader.py`
**Schedule:** Every 30 min during market hours via cron

---

## System Overview

### Trading Hours (Jess's time - CST)
- **Pre-market:** 7:00 AM - 8:30 AM
- **Market open:** 8:30 AM - 3:00 PM  
- **After-hours:** 3:00 PM - 5:00 PM

### The Edge
1. **Speed** - Monitor and react faster than manual trading
2. **Discipline** - No emotions, strict rules
3. **News reaction** - Catch moves from breaking news
4. **Momentum riding** - Jump on trends early

---

## Strategy 1: Momentum + VWAP Swing (ACTIVE — Grok v2)

**Concept:** Find stocks with 2%+ momentum, confirm with VWAP, swing hold 1-3 days

**Entry Rules (Grok-optimized):**
- Stock up 2%+ from previous close (lowered from 3%)
- Volume 1.5x+ average
- Price ABOVE VWAP (bullish confirmation)
- Max $45 per position (45% of equity)

**Exit Rules (Grok-optimized):**
- Stop loss: -2% (tightened from -3%, via bracket order)
- Trailing stop: 2.5% (replaces fixed take profit)
- Safety net: +10% take profit limit
- Hold 1-3 days (swing, not day trade)

**Bracket Orders:** Stop loss auto-attached at entry via Alpaca bracket orders

---

## Strategy 2: Gap & Go

**Concept:** Stocks that gap up at open often continue

**Entry Rules:**
- Gap up 4%+ at open
- First 5-min candle closes green
- Buy on break of first 5-min high

**Exit Rules:**
- Take profit: +8-12%
- Stop loss: Below first 5-min low
- Trail stop after +5%

---

## Strategy 3: News Catalyst

**Concept:** Major news = major moves

**Catalysts to watch:**
- Earnings beats/misses
- FDA approvals
- Contract wins
- Analyst upgrades
- CEO/major personnel changes

**Entry:** As fast as possible after news
**Exit:** Quick scalp +3-5% or ride with trail stop

---

## Watchlist

### High-Momentum Stocks (Grok-optimized watchlist)
- NVDA - AI leader, big swings
- TSLA - Always volatile
- AMD - Semiconductor momentum
- META - Tech giant, news-driven
- PLTR - High beta, retail favorite
- AAPL - High liquidity, smoother action (Grok: added)
- MSFT - High liquidity, smoother action (Grok: added)
- ~~SOFI~~ - Removed (Grok: too low liquidity for $100 account)

### ETFs (safer, for swing trades)
- SPY - S&P 500
- QQQ - Nasdaq 100
- SOXL - 3x Semiconductors (HIGH RISK)

---

## Position Sizing (Grok-optimized)

| Account Size | Max Position | Stop Loss $ | Cash Buffer |
|--------------|--------------|-------------|-------------|
| $100 | $45 (45%) | $0.90 (2%) | $10 |
| $200 | $90 (45%) | $1.80 (2%) | $10 |
| $500 | $200 (40%) | $4.00 (2%) | $20 |
| $1000+ | $300 (30%) | $6.00 (2%) | $50 |

---

## Daily Routine

### Pre-Market (7:00 AM)
1. Check overnight news
2. Identify gappers
3. Set alerts for key levels
4. Plan 2-3 potential trades

### Market Open (8:30 AM)
1. Watch first 5 minutes
2. Identify momentum leaders
3. Execute if setup triggers

### Mid-Day (11:00 AM - 1:00 PM)
1. Reduced trading (choppy period)
2. Review positions
3. Adjust stops

### Afternoon (1:30 PM - 3:00 PM)
1. Watch for late-day momentum
2. Close day trades by 2:30 PM
3. EOD review

---

## Risk Rules (NON-NEGOTIABLE)

1. **Max 2 trades per day** (while learning)
2. **Always use stop loss**
3. **Never average down on losers**
4. **Take profits - don't get greedy**
5. **No trading first 5 min (let dust settle)**
6. **Stop trading after 2 losses in a day**

---

## Trade Log

| Date | Ticker | Direction | Entry | Exit | Shares | P/L $ | P/L % | Notes |
|------|--------|-----------|-------|------|--------|-------|-------|-------|
| | | | | | | | | |

---

## Performance Tracking

### Weekly Stats
| Week | Trades | Wins | Losses | Net P/L | Win Rate |
|------|--------|------|--------|---------|----------|
| | | | | | |

---

## Automation Status

- [x] API connected ✅
- [x] Account verified ($100, LIVE) ✅
- [x] Momentum scanner built ✅
- [x] Auto-execution (Level 2 semi-auto) ✅
- [x] Alert system (iMessage to Jess) ✅
- [x] Stop loss / take profit automation ✅
- [x] Daily loss limit (2 max) ✅
- [x] Cron job (every 30 min, market hours) ✅
- [ ] News catalyst monitor
- [ ] Gap & Go strategy

---

## Notes

- Start manual/semi-auto, then automate winners
- Journal every trade - learn from mistakes
- Scale up ONLY after consistent profits
- This is a marathon, not a sprint
