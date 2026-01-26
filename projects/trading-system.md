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

## Strategy 1: Momentum Scanner

**Concept:** Find stocks moving 3%+ with high volume, ride the wave

**Entry Rules:**
- Stock up 3-5% from previous close
- Volume 2x+ average
- RSI not overbought (< 70)
- No major resistance nearby

**Exit Rules:**
- Take profit: +5-10% from entry
- Stop loss: -3% from entry
- Time stop: Exit by 2:30 PM if flat

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

### High-Momentum Stocks (volatile, good for day trades)
- NVDA - AI leader, big swings
- TSLA - Always volatile
- AMD - Semiconductor momentum
- META - Tech giant, news-driven
- PLTR - High beta, retail favorite
- SOFI - Fintech, volatile

### ETFs (safer, for swing trades)
- SPY - S&P 500
- QQQ - Nasdaq 100
- SOXL - 3x Semiconductors (HIGH RISK)

---

## Position Sizing

| Account Size | Max Position | Stop Loss $ |
|--------------|--------------|-------------|
| $100 | $50 (50%) | $2.50 (5%) |
| $200 | $100 (50%) | $5.00 (5%) |
| $500 | $200 (40%) | $10.00 (5%) |
| $1000+ | $300 (30%) | $15.00 (5%) |

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
