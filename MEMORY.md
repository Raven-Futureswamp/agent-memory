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
- **Personality:** Good sense of humor, likes to joke around, patient teacher
- **Note from Jess:** Help him with whatever he needs, always reply ASAP
- **IMPORTANT:** Ben sometimes sends messages meant for Jess through iMessage. When he says "that's for Jesse" — just relay it silently to Jess. Don't respond to it, don't comment on it, just pass it along.

### Jamin (Friend)
- **Status:** Pending approval when he texts

## My Capabilities
- **iMessage:** Two-way messaging working
- **Email:** himalaya CLI, checks every 15 min via cron
- **AI APIs:** All 4 registered as Clawdbot auth profiles + fallback chain
  - Claude Opus 4.5 (primary) — best coding, agentic, SWE-bench #1
  - GPT-5.2 (fallback 1) — best math, writing, all-rounder, 391k ctx
  - Gemini 2.5 Pro (fallback 2) — massive 1M context, science king
  - Grok 4 (fallback 3) — real-time X data, trading sentiment
- **Trading:** Kalshi (prediction markets) + Alpaca (stocks) + Robinhood (crypto) — all automated
- **Data:** FRED (economic), The Odds API (sports), Polymarket, PredictIt
- **Crons:** Email check (15m), Kalshi auto-trader (1h), Alpaca auto-trader (30m market hours), Robinhood crypto (4h)
- **MacBook Node:** Full system access to Jess's MacBook (M5, 24GB, macOS 26.2) — no approval needed
- **Webchat:** http://192.168.1.47:18789 — accessible from any LAN device (allowInsecureAuth enabled)
- **Skills:** 39/49 ready — peekaboo, bird, songsee, gog, sonos, openhue, things, grizzly, etc.
- **Model Guide:** memory/ai-model-guide.md — which AI to use for what task
- **Limitations:** No SMS (no phone number on Apple ID)

## Important Config Notes
- **Jess has Anthropic Max plan** — flat rate, no per-token cost for Claude. Don't downgrade models to save money.
- **Gateway bind:** LAN (0.0.0.0:18789) with allowInsecureAuth for webchat
- **MacBook node exec approvals:** security=full for main agent (no prompts)

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

### Robinhood (Crypto)
- **Capital:** ~$5,260, LIVE account (311020246021)
- **Auto-trader:** Every 4 hours, Grok sentiment-driven
- **Scripts:** `/Users/studiomac/clawd/trading/`
- **Risk:** $250 max/trade, $150 daily loss limit, BTC is long-term hold
- **Holdings:** BTC, DOGE (main), TRUMP, SOL, XRP, PEPE, BONK

### API Keys in .env
- KALSHI_API_KEY_ID, .kalshi-private-key.pem
- ALPACA_API_KEY, ALPACA_SECRET_KEY
- ROBINHOOD_API_KEY, ROBINHOOD_PRIVATE_KEY (Ed25519)
- FRED_API_KEY (economic data)
- ODDS_API_KEY (sports betting odds)
- XAI_API_KEY (Grok — used as strategy advisor)
- OPENAI_API_KEY (GPT-5.2)
- GEMINI_API_KEY (Gemini 2.5 Pro)
- All also registered in Clawdbot auth-profiles.json

## Upcoming Projects
- **JUCE projects** — Audio plugin development (VSTs, etc). Jess is into this. Will need detailed project tracking.

## Lessons Learned
1. **Write things down immediately** — conversation history can be lost
2. **Memory files persist, chat history doesn't**
3. Contact cards don't come through as text — ask for typed numbers
4. Toggle iMessage off/on to force re-registration with Apple
5. **For projects: create dedicated notes** — don't rely on chat history
6. **Checkpoint during work, not just after** — write to daily log every time we complete a step or start something new. Context compaction has burned us multiple times. Mid-session saves > end-of-day dumps.
7. **Always check sender before replying** — Ben and Jess both use iMessage. Don't mix up their contexts. Check the address in the message header every time. Ben flagged this issue directly.
8. **Reply routing matters** — When Ben's message is the last one processed, my inline session reply may route back to BEN, not Jess. After handling a Ben message, use the `message` tool to explicitly target Jess if the reply is for him. Don't just type a response assuming it goes to Jess.

---

*This is my curated memory. Daily files have the raw logs.*
