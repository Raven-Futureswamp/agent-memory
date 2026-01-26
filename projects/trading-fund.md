# Trading Fund Project 💰

*Goal: Generate capital for studio build-out + Airbnb cabins*

Started: 2025-06-28

---

## The Vision

Use AI-assisted trading and prediction markets to generate funds for:
1. **Music studio build-out** — Jess's audio production facility
2. **Airbnb cabins** — Rental income on the property

---

## Platforms & Strategies

### 1. Kalshi (Prediction Markets) ⭐ PRIMARY FOCUS

**What it is:** US-regulated prediction market (CFTC-regulated). Buy shares in outcomes of future events. Shares pay $1 if correct, $0 if wrong.

**Official Python SDK:** `kalshi-python`
- Install: `pip install kalshi-python`
- API Keys: Stored in `.env` and `.kalshi-private-key.pem`

**Account Status:** ✅ CONNECTED
- Balance: $100
- API verified working 2026-01-25

**Strategies:**

#### A. Near-Certain Outcomes (Best for starting)
- Find contracts with mispriced probabilities
- Example: Something 95% certain trading at 80¢ = free 20¢ per share
- Focus on: economic data releases, weather events, sports, politics
- Use external data (FiveThirtyEight, Reuters, expert forecasts) to assess true probability

#### B. Event-Driven Trading
- Trade on breaking news before market prices it in
- Need real-time news feeds (Twitter API, news APIs)
- Fast execution required

#### C. Market Making (Advanced)
- Provide liquidity by placing buy/sell orders with a spread
- Profit from the spread when others trade against you
- Requires automated bot and constant monitoring

**Advantages over Polymarket:**
- Fully US-legal (CFTC regulated)
- No crypto wallet needed
- Real USD, not USDC
- Clean API with official Python SDK

~~### OLD: Polymarket~~ — BLOCKED for US users

---

### 2. Alpaca (Stock Trading) ⭐ ACTIVE

**What it is:** Commission-free stock/crypto trading with a real API designed for automation

**Advantages:**
- Paper trading free for everyone (test strategies risk-free)
- Real API with Python SDK
- Fractional shares (buy $1 of any stock)
- Crypto trading 24/7
- Fully regulated, clean

**Best for:**
- More traditional trading strategies
- Swing trading based on technical signals
- Dollar-cost averaging automation

---

### 3. Robinhood — NOT RECOMMENDED

- No official API
- Against ToS to automate
- Account ban risk
- Use Alpaca instead if we want stocks

---

## Next Steps

### Phase 1: Setup ✅ COMPLETE
- [x] ~~Create Polymarket account~~ (blocked - US users prohibited)
- [x] Create Alpaca account ✅
- [x] Create Kalshi account ✅
- [x] API keys configured ✅
- [x] Funded: $100 Alpaca (LIVE), $100 Kalshi

### Phase 2: Research & Testing
- [ ] Build script to scan Kalshi for mispriced contracts
- [ ] Set up news monitoring for event-driven trades
- [ ] Build Alpaca momentum scanner
- [ ] Track all trades in spreadsheet

### Phase 3: Live Trading
- [ ] Start with small positions on "sure things"
- [ ] Scale up as we prove edge
- [ ] Diversify across multiple strategies

---

## Risk Management Rules

1. **Never bet more than 10% on single contract**
2. **Start small** — prove the strategy works before scaling
3. **Track everything** — spreadsheet with all trades, fees, P&L
4. **Platform risk** — crypto platforms can have issues, don't keep life savings there
5. **"Sure things" aren't 100%** — black swans happen

---

## Capital Allocation

Initial investment: $200 total
- Kalshi: $100 (prediction markets)
- Alpaca: $100 (stocks)

Starting small, scale up after proving edge.

---

## Notes

*Add ongoing observations, lessons learned, trade ideas here*

