# Kalshi Prediction Market Trading 🎯

*Automated prediction market trading on Kalshi*

Started: 2026-01-25
Platform: Kalshi (CFTC-regulated, US-legal)
Capital: $100

---

## Account Status

- **API Connected:** ✅ Yes
- **Balance:** $64.58 cash + ~$34 in positions = ~$99 total
- **Note:** Selling Trump ends Fed (2029 too long) — 5/21 filled, 16 resting at 90¢
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
- ✅ **Position sizing** — Max 10% of capital per trade ($10) — smaller, diversified
- ✅ **Fee accounting** — Min 3¢ edge after fees
- ✅ **Priority tiers** — HOT (short-term) → Medium → Long-term
- ✅ **ROI calculation** — Shows % return per trade
- ✅ **Multi-source arbitrage** — Cross-references Kalshi vs Polymarket, PredictIt
- ✅ **Sports odds** — The Odds API with multi-book consensus
- ✅ **FRED econ data** — Fed rate, CPI, GDP, unemployment
- ✅ **CPI probability model** — FRED 12-month MoM distribution → probability thresholds
- ✅ **Catalyst calendar** — Flags Fed meetings, CPI releases, jobs reports within 48h
- ✅ **Stop-loss / Take-profit** — Auto-exit at -15% / +20%
- ✅ **Position count limit** — Max 5-6 smaller positions (diversified)

## Arbitrage Scanner v2.1

**Script:** `scripts/kalshi/arbitrage_v2.py`
**Run:** `cd ~/clawd && source .venv/bin/activate && python3 scripts/kalshi/arbitrage_v2.py`

**What it does:**
- Fetches all Kalshi markets closing within 60 days (vol ≥ 500)
- Cross-references against Polymarket + PredictIt prices
- Strict keyword matching only (no fuzzy = no junk)
- CPI probability model (FRED 12-month MoM distribution → Gaussian + empirical blend)
- Catalyst calendar (Fed meetings, CPI releases, jobs reports within 48h)
- Sports odds multi-book consensus (American → implied probability, flag >5% gap)
- Expanded keyword rules: CPI ranges, Fed decisions, GDP, unemployment, weather, NFL/NBA teams

**Sources:**
| Source | Status | Key Needed? |
|--------|--------|-------------|
| Kalshi | ✅ Live | API key (have it) |
| Polymarket | ✅ Live | None |
| PredictIt | ✅ Live | None |
| The Odds API | ✅ Live | Free key added |
| FRED (Fed rates, CPI, GDP, unemployment) | ✅ Live | Free key added |

**v2.1 Enhancements (Grok recommendations 2026-01-25):**
1. **CPI Probability Model** — Fetches 12 months CPI MoM from FRED, calculates empirical + Gaussian distribution, compares vs Kalshi CPI market prices. Flags gaps >5%.
2. **Catalyst Calendar** — Hardcoded FOMC, CPI release, and jobs report dates. Flags when within 48h (high-opportunity windows).
3. **Better Sports Odds** — Averages across ALL bookmakers for consensus probability. Only matches game outcome markets (filters prop bets). Flags >5% gap vs Kalshi.
4. **Expanded Keyword Rules** — CPI monthly ranges (0.0-0.4%), Fed rate decisions (hold/cut/hike), GDP growth ranges, unemployment thresholds, weather (hurricane, temperature, cities), NFL teams (14 teams), NBA teams (10 teams), tariffs, debt ceiling.

**Last scan (2026-01-25 21:14):**
- 3,094 short-term Kalshi markets (<60 days)
- 200 Polymarket + 760 PredictIt + 80 sportsbook lines
- FRED: Rate 3.5-3.75% | CPI MoM +0.307% (mean: 0.249%, stdev: 0.139%) | Unemp 4.4% | GDP 4.4%
- CPI Model: 6 thresholds evaluated (>0.0% through >0.5%)
- 14 opportunities found (10 CPI model-based)

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

## Risk Rules (Updated per Grok recs 2026-01-25)

- **Max 10% per trade ($10)** — smaller positions, more diversified (was 20%/$20)
- **Max 60% in positions** — allows 5-6 smaller positions simultaneously
- **Max 6 positions** — enforced in auto-trader
- **Stop-loss: -15%** — auto-exit if position value drops 15% from entry
- **Take-profit: +20%** — auto-exit if position value rises 20% from entry
- **Min spread: 5 pts** between platforms
- **Min ROI: 8%**
- **Min volume: 1,000**
- **Min 3¢ edge** after Kalshi fees
- **Short-term only** — <60 days to close
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

**Risk Rules (updated 2026-01-25):**
- Spread > 5 pts between platforms
- ROI > 8%
- Volume > 1,000
- **Max $10 per trade (10% of capital)** — was $20/20%
- Max 60% of capital in positions at once
- **Max 6 positions** — target 5-6 smaller diversified bets
- Short-term only (<60 days)
- Min 3¢ edge after fees
- Keeps $5 cash buffer
- **Stop-loss: -15%** — auto-exits if position value drops
- **Take-profit: +20%** — auto-exits if position value rises

**How it works:**
1. Checks existing positions for stop-loss/take-profit triggers → auto-exits
2. Scans Kalshi vs Polymarket + PredictIt + Odds API + CPI model every hour
3. Checks FRED for economic context + catalyst calendar
4. If opportunity passes ALL risk rules → auto-executes
5. Alerts Jess via iMessage with trade details (entries + exits)
6. Jess can say "kalshi undo" to reverse within 1 hour

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
| 2026-01-25 | Trump ends Fed | SELL NO | 90¢ | 5/21 | +$4.46 | ⏳ 16 RESTING |
| 2026-01-25 | DOGE cuts $1T | NO | 88¢ | 1 | $0.88 | ⏳ PARTIAL (21 pending) |

**Total Invested:** $39.45
**Potential Payout:** $47.00
**Potential Profit:** $7.55 (19.1% ROI)

---

## Notes

### ⚠️ Position Review: "Trump Ends Fed" (NO @ 92¢)
**Grok recommends exiting this position.** Reasoning: 92¢ for NO leaves only 8¢ upside ($1.68 potential profit on 21 contracts) while risking $19.32 if it flips to YES. The risk/reward ratio is unfavorable. Consider selling this position to free up capital for higher-ROI CPI/economic trades.

**DO NOT auto-exit** — manual decision required by Jess.

### Grok v2 Recommendations (2026-01-25) — ALL IMPLEMENTED
1. ✅ Exit long-dated positions (>12mo) — selling Trump/Fed 2029
2. ✅ Smaller bets: $10 per trade (10%) instead of $20 (20%)
3. ✅ Add CPI probability model using FRED historical data (12-month MoM distribution)
4. ✅ Event-driven trading: catalyst calendar (Fed meetings, CPI releases, jobs reports within 48h)
5. ✅ Better sports odds: multi-book consensus, American odds → implied probability, >5% gap flagging
6. ✅ Add stop-loss (-15%) and take-profit (+20%) auto-exit monitoring
7. ❌ Don't market-make — $100 too small
8. ✅ More keyword rules: CPI ranges (0.0-0.4%), Fed decisions (hold/cut/hike), GDP growth, unemployment, weather (hurricane/temperature/cities), NFL (14 teams), NBA (10 teams)
9. ✅ Trade more frequently with smaller bets around catalysts (max 6 positions)
10. ✅ Max 12 month positions only (60-day scanner window)

**Rule change:** No positions resolving beyond 12 months.

