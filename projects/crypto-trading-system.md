# Crypto Trading System 🚀

*Goal: Build an automated/semi-automated crypto trading system that compounds gains*

Started: 2025-06-28
Capital: $100 (starting)

---

## System Architecture

### The Edge
1. **Speed** - Raven monitors 24/7, executes faster than humans
2. **Attention** - Multiple data sources processed simultaneously
3. **Discipline** - No emotions, strict rules
4. **Compounding** - Every win reinvested

### Data Sources to Monitor
- [ ] Price movements (Alpaca API)
- [ ] News feeds (crypto-specific)
- [ ] Twitter/X sentiment (via Grok)
- [ ] Volume spikes
- [ ] Technical indicators (RSI, MACD, Bollinger)

### Trading Rules (Draft)
1. **Entry signals:**
   - Momentum: 5%+ move with volume confirmation
   - Oversold bounce: RSI < 30 reversing
   - News catalyst: Major positive news

2. **Exit signals:**
   - Target hit: +10-15% gain
   - Stop loss: -5% from entry
   - Momentum fade: Volume drying up

3. **Position sizing:**
   - Max 50% of capital per trade
   - Scale in on confirmation
   - Never go all-in

---

## Phase 1: Setup ✅
- [x] Alpaca account created
- [x] API keys configured
- [ ] Enable crypto trading (Jess needs to do in dashboard)
- [ ] Test crypto buy/sell

## Phase 2: Monitoring System
- [ ] Build price alert system
- [ ] Set up news monitoring
- [ ] Create momentum scanner
- [ ] Backtest strategies

## Phase 3: Automation
- [ ] Define clear trade rules
- [ ] Build execution logic
- [ ] Paper trade for 1 week
- [ ] Go live with real trades

---

## Trade Log

| Date | Asset | Direction | Entry | Exit | P/L | Notes |
|------|-------|-----------|-------|------|-----|-------|
| | | | | | | |

---

## Daily Review
*Track what's working, what's not*

---

## Available Crypto on Alpaca
- BTC/USD - Bitcoin
- ETH/USD - Ethereum
- SOL/USD - Solana
- AVAX/USD - Avalanche
- LTC/USD - Litecoin
- XRP/USD - Ripple
- LINK/USD - Chainlink
- UNI/USD - Uniswap
- SUSHI/USD - SushiSwap
- DOT/USD - Polkadot

---

## Notes
- Start with BTC/ETH (most liquid, most news coverage)
- Expand to altcoins as system matures
- Weekend = crypto only time (stocks closed)
