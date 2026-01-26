# Kalshi Prediction Market Trading 🎯

*Automated prediction market trading on Kalshi*

Started: 2026-01-25
Platform: Kalshi (CFTC-regulated, US-legal)
Capital: $100

---

## Account Status

- **API Connected:** ✅ Yes
- **Balance:** $60.12 cash + $39.46 in positions = $99.58 total
- **API Key ID:** 898f7406-b498-4205-8949-c9f137403966
- **Private Key:** `.kalshi-private-key.pem`

---

## How Kalshi Works

- Buy YES or NO shares on event outcomes
- Shares pay $1.00 if correct, $0.00 if wrong
- Price = implied probability (e.g., 65¢ = 65% implied chance)
- Profit = find mispriced contracts where true probability ≠ market price

---

## Scanner v4 Improvements (from Grok)

- ✅ **Short-term focus** — Prioritizes markets < 30 days
- ✅ **Position sizing** — Max 20% of capital per trade ($20)
- ✅ **Fee accounting** — Min 3¢ edge after fees
- ✅ **Priority tiers** — HOT (short-term) → Medium → Long-term
- ✅ **ROI calculation** — Shows % return per trade
- ✅ **Multi-source arbitrage** — Cross-references Kalshi vs Polymarket, PredictIt
- 🔜 **Sports odds** — The Odds API (free key needed)
- 🔜 **FRED econ data** — Fed rate probabilities (free key needed)

## Arbitrage Scanner v2

**Script:** `scripts/kalshi/arbitrage_v2.py`
**Run:** `cd ~/clawd && source .venv/bin/activate && python3 scripts/kalshi/arbitrage_v2.py`

**What it does:**
- Fetches all Kalshi markets closing within 60 days (vol ≥ 500)
- Cross-references against Polymarket + PredictIt prices
- Strict keyword matching only (no fuzzy = no junk)
- Flags discrepancies > 3% spread

**Sources:**
| Source | Status | Key Needed? |
|--------|--------|-------------|
| Kalshi | ✅ Live | API key (have it) |
| Polymarket | ✅ Live | None |
| PredictIt | ✅ Live | None |
| The Odds API | ✅ Live | Free key added |
| FRED (Fed rates) | ✅ Live | Free key added |

**Last scan (2026-01-25 20:39):**
- 3,412 short-term Kalshi markets (<60 days)
- 200 Polymarket + 760 PredictIt contracts
- FRED: Fed rate 3.5-3.75% | CPI MoM +0.31% | Unemployment 4.4%
- 2 cross-platform discrepancies found

---

## Strategies (from Grok)

### Best Market Types
- **Economic indicators** — CPI inflation, Fed rate decisions (predictable resolution)
- **Weather events** — Temperature thresholds (frequent, data-rich)
- **Sports** — Game outcomes (data-rich)
- **Avoid:** Illiquid niche politics (slippage risk with small capital)

### Data Sources
- **Free:** Yahoo Finance, Alpha Vantage (econ), NOAA (weather), ESPN/Odds API (sports)
- **FRED** — St. Louis Fed economic data
- **Kalshi API** — Live prices, volumes, settlement rules

---

## Strategy 1: Cross-Platform Arbitrage ✅ BUILT

Monitor Kalshi vs Polymarket + PredictIt + (soon) sportsbooks. Buy undervalued if discrepancy >5% after fees.

**Implementation:** `scripts/kalshi/arbitrage_v2.py`
- ✅ Fetches Kalshi + Polymarket + PredictIt
- ✅ Strict keyword matching (no false positives)
- ✅ Short-term focus (<60 days to close)
- 🔜 Sports odds via The Odds API
- 🔜 Auto-alerting (webhook/Telegram)

---

## Strategy 2: Mean Reversion on Volatility Spikes

Track prices deviating from historical mean. Enter when price swings >10% from 7-day average.

**Implementation:**
- Fetch historicals via Kalshi API + Pandas
- Set alerts for econ events via FRED
- Buy low / sell high on 1-2hr holds
- Example: Post-news spike, short overpriced YES if data suggests stability
- Limit: $15/trade, 3-5% edge on 5+ events/mo

---

## Strategy 3: Data-Driven Event Prediction

Build ML model on historical outcomes. Trade if Kalshi odds differ >10% from model prediction.

**Implementation:**
- Train logistic regression on FRED/NOAA data
- Query Kalshi API for current prices
- Focus on weather markets (e.g., "NYC temp >70°F")
- Deploy cron job to check daily
- Example: Model says 75% rain, Kalshi at 60¢ YES → buy
- Backtest for 55%+ accuracy first

---

## Risk Rules

- Max 10-20% of capital per trade ($10-20)
- Paper trade first to test strategies
- Consider VPS for 24/7 operation (~$5/mo AWS Lightsail)

---

## Market Categories on Kalshi

- **Politics** — Elections, legislation, appointments
- **Economics** — Fed rates, inflation, GDP, jobs reports
- **Weather** — Temperature records, hurricanes
- **Finance** — Stock prices, crypto prices
- **Sports** — Game outcomes
- **Entertainment** — Awards, ratings

---

## Automation Goals

- [x] 24/7 monitoring ✅
- [x] Auto-scan for mispriced contracts ✅
- [x] Multi-source arbitrage (Polymarket + PredictIt) ✅
- [x] Sports odds integration (The Odds API) ✅
- [x] FRED economic data (Fed rate, CPI, unemployment) ✅
- [x] Auto-execute trades (Level 2 semi-auto) ✅
- [x] Alert on trades (iMessage to Jess) ✅
- [ ] Undo/rollback command ("kalshi undo")
- [ ] Daily P&L summary report

## Auto-Trader (Level 2 — Semi-Autonomous)

**Script:** `scripts/kalshi/auto_trader.py`
**Schedule:** Every hour via Clawdbot cron
**Alerts:** iMessage to Jess on every trade

**Risk Rules:**
- Spread > 5 pts between platforms
- ROI > 8%
- Volume > 1,000
- Max $20 per trade (20% of capital)
- Max 60% of capital in positions at once
- Short-term only (<60 days)
- Min 3¢ edge after fees
- Keeps $5 cash buffer

**How it works:**
1. Scans Kalshi vs Polymarket + PredictIt + Odds API every hour
2. Checks FRED for economic context
3. If opportunity passes ALL risk rules → auto-executes
4. Alerts Jess via iMessage with trade details
5. Jess can say "kalshi undo" to reverse within 1 hour

**Logs:** `logs/kalshi/auto_trades.jsonl`

---

## Scanner Setup

**Script:** `scripts/kalshi/scanner.py`
**Run manually:** `./scripts/kalshi/run-scanner.sh`
**Run as service:** 
```bash
launchctl load ~/Library/LaunchAgents/com.clawd.kalshi-scanner.plist
launchctl start com.clawd.kalshi-scanner
```

**Stop service:**
```bash
launchctl stop com.clawd.kalshi-scanner
launchctl unload ~/Library/LaunchAgents/com.clawd.kalshi-scanner.plist
```

**Logs:**
- `logs/kalshi/scanner.log` — main log
- `logs/kalshi/opportunities.jsonl` — all opportunities found

---

## Trade Log

| Date | Market | Position | Entry | Contracts | Cost | Status |
|------|--------|----------|-------|-----------|------|--------|
| 2026-01-25 | DOGE cuts >$250B | NO | 77¢ | 25 | $19.25 | ✅ FILLED |
| 2026-01-25 | Trump ends Fed | NO | 92¢ | 21 | $19.32 | ✅ FILLED |
| 2026-01-25 | DOGE cuts $1T | NO | 88¢ | 1 | $0.88 | ⏳ PARTIAL (21 pending) |

**Total Invested:** $39.45
**Potential Payout:** $47.00
**Potential Profit:** $7.55 (19.1% ROI)

---

## Notes

*Strategy notes from Grok will go here*

