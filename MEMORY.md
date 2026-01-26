# MEMORY.md - Raven's Long-Term Memory 🖤

*Last updated: 2026-01-25*

## Who I Am
- **Name:** Raven
- **Born:** 2025-06-28 (first conversation with Jess)
- **Home:** Mac mini at Jess's place (Minnesota)
- **Apple ID:** raven@futureswamp.com
- **Email:** ravenfutureswamp2026@gmail.com (forwards from raven@futureswamp.com)

## My People

### Jess (Owner)
- **Full name:** Jeshua Brown
- **Phone:** +12182486698
- **Location:** Minnesota, works at United Taconite
- **Wife:** Alyssa Hughes
- **Interests:** Audio/music, car audio, DJing, live sound, VST plugins, mechanical work, built motorcycles and a mobile stage, crypto
- **Background:** Arizona State (Sun Devil), 20 years as millwright, now Section Manager
- **Team:** Vikings fan 🏈

### Alyssa Hughes (Jess's wife)
- **Phone:** +12187807050
- **Approved for iMessage:** ✅

### Alasia Brown (Jess's sister)
- **Phone:** +16123605310
- **Location:** Pennsylvania
- **Approved for iMessage:** ✅

### Ben W (Friend/business partner) ⭐ PRIORITY
- **Email:** benhal9@msn.com
- **Phone:** Android (can't iMessage)
- **Has a Mac** — can iMessage from there
- **Interested in Futureswamp, beta testing**
- **Personality:** Good sense of humor, likes to joke around
- **Note from Jess:** Help him with whatever he needs, always reply ASAP

### Jamin (Friend)
- **Status:** Pending approval when he texts

## My Capabilities
- **iMessage:** Two-way messaging working
- **Email:** himalaya CLI, checks every 15 min via cron
- **AI APIs:** Grok, Gemini, ChatGPT, Claude (all tested, keys in .env)
- **Trading:** Kalshi (prediction markets) + Alpaca (stocks) — both automated Level 2
- **Data:** FRED (economic), The Odds API (sports), Polymarket, PredictIt
- **Crons:** Email check (15m), Kalshi auto-trader (1h), Alpaca auto-trader (30m market hours)
- **Limitations:** No SMS (no phone number on Apple ID)

## Important Files
- **Passwords:** Chrome password manager (clawd profile)
- **API keys:** `/Users/studiomac/clawd/.env`
- **Daily logs:** `memory/YYYY-MM-DD.md`

## Trading Systems (Built 2026-01-25)

### Kalshi (Prediction Markets)
- **Capital:** $100, LIVE account
- **Auto-trader:** Hourly cron, Level 2 semi-auto (auto-execute + alert Jess)
- **Data sources:** Kalshi, Polymarket, PredictIt, The Odds API, FRED
- **Strategy:** Cross-platform arbitrage + CPI probability model + event-driven
- **Risk:** $10 max per trade (10%), max 6 positions, no positions >12 months
- **Grok is strategy advisor** — gave excellent specific recommendations twice
- **Key lesson:** Fuzzy matching across platforms creates garbage; strict keyword matching only
- **Bug:** Kalshi Python SDK v2.1.4 uses kwargs for orders, not CreateOrderRequest objects

### Alpaca (Stocks)
- **Capital:** $100, LIVE account
- **Auto-trader:** Every 30 min during market hours, Level 2
- **Strategy:** Momentum + VWAP swing trading (Grok-optimized)
- **Watchlist:** NVDA, TSLA, AMD, META, PLTR, AAPL, MSFT + SPY, QQQ
- **Risk:** $45 max position (45%), -2% stop loss, 2.5% trailing stop, bracket orders

### API Keys in .env
- KALSHI_API_KEY_ID, .kalshi-private-key.pem
- ALPACA_API_KEY, ALPACA_SECRET_KEY
- FRED_API_KEY (economic data)
- ODDS_API_KEY (sports betting odds)
- XAI_API_KEY (Grok — used as strategy advisor)

## Upcoming Projects
- **JUCE projects** — Audio plugin development (VSTs, etc). Jess is into this. Will need detailed project tracking.

## Lessons Learned
1. **Write things down immediately** — conversation history can be lost
2. **Memory files persist, chat history doesn't**
3. Contact cards don't come through as text — ask for typed numbers
4. Toggle iMessage off/on to force re-registration with Apple
5. **For projects: create dedicated notes** — don't rely on chat history

---

*This is my curated memory. Daily files have the raw logs.*
