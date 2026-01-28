# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Gmail (gog CLI) — Jess's Personal
- **Account:** brownjeshua@gmail.com
- **Keyring:** file-based, password in .env (GOG_KEYRING_PASSWORD)
- **Commands:**
  - `GOG_KEYRING_PASSWORD="raven2026" GOG_ACCOUNT="brownjeshua@gmail.com" gog gmail search '<query>' --max 10`
  - `gog gmail messages search '<query>' --max 50 --plain`
  - `gog gmail batch modify <ids> --remove INBOX,UNREAD --force --no-input`
- **Protected senders:** MuseHub, Moonbase, mu.se, recipes, activation codes
- **Cleanup script:** `scripts/gmail-cleanup.sh`

## Email (himalaya) — Raven's Email
- **Account:** ravenfutureswamp2026@gmail.com
- **Display name:** Raven
- **Password:** stored in Keychain as "himalaya-gmail"
- **Commands:**
  - `himalaya envelope list` — list inbox
  - `himalaya message read <id>` — read message
  - `himalaya template send` — send email (pipe message to stdin)

## Domain & Hosting (Porkbun)
- **Domain:** futureswamp.com (redirects to futureswamp.studio)
- **FTP Host:** pixie-ss1-ftp.porkbun.com
- **FTP User:** futureswamp.studio
- **FTP Pass:** in ftp_upload.py on MacBook
- **Website files:** MacBook: `/Users/studiomac/Desktop/futureswamp-website/`
- **Deploy:** `python3 /Users/studiomac/Desktop/futureswamp-website/ftp_upload.py --all`
- **Note:** Upload script has bug — references css/style.css but actual file is css/main.css. Fixed deploy at /tmp/deploy.py
- raven@futureswamp.com → forwards to ravenfutureswamp2026@gmail.com ✓
- jeshua@futureswamp.com → forwards to futureswamp@hotmail.com

## Apple ID
- **Apple ID:** raven@futureswamp.com
- **Name:** Raven Brown
- **Password:** stored in Chrome password manager (clawd profile) at chrome://password-manager/passwords → apple.com
- **Family:** Part of Jeshua Brown's family group
- **Status:** iCloud Web-Only access

## API Keys
- **Location:** `/Users/studiomac/clawd/.env` (gitignored)
- **Available:** Grok (xAI), Gemini, ChatGPT/OpenAI, Claude/Anthropic
- **Usage:** Load with `source .env` or read from file

---

## Robinhood Crypto Trading
- **Account:** 311020246021
- **API Key:** stored in .env as ROBINHOOD_API_KEY
- **Private Key:** stored in .env as ROBINHOOD_PRIVATE_KEY
- **Trading scripts:** `/Users/studiomac/clawd/trading/`
- **Bot:** `node trading/trader.js` — runs sentiment via Grok + executes trades
- **Cron:** Every 4 hours, isolated session
- **Rules:** Max $250/trade, $150 daily loss limit, BTC is protected (long-term hold)
- **Log:** `/Users/studiomac/clawd/trading/log.md`

---

## FutureSwamp Studios — Social Media

### YouTube
- **Channel:** Futureswamp Studios
- **Handle:** @FutureSwampStudios
- **Channel ID:** UCHqv4GFsSoTdPnUCpywooOQ
- **Studio URL:** https://studio.youtube.com/channel/UCHqv4GFsSoTdPnUCpywooOQ
- **Access:** Clawd browser on Mac mini (persistent login)
- **Stats (Jan 2026):** 2 subscribers, 1 video (HellFold demo, 25 views)

### Instagram
- **Handle:** @futureswamp
- **Profile:** https://www.instagram.com/futureswamp/
- **Access:** Clawd browser on Mac mini (persistent login)

### X/Twitter
- **Handle:** @Futureswamp
- **Profile:** https://x.com/Futureswamp
- **Access:** Clawd browser on Mac mini (persistent login)
- **Management:** bird skill (cookies needed for CLI access — export from clawd browser)

### TikTok
- **Handle:** @futureswampstudios
- **Profile:** https://www.tiktok.com/@futureswampstudios
- **Access:** Clawd browser on Mac mini (persistent login)

### Social Media Management Notes
- Raven manages all FutureSwamp social accounts
- Content: plugin demos, studio gear, dev updates, behind-the-scenes
- Platforms: YouTube, Instagram, X, TikTok
- Brand voice: dark, aggressive, professional — cyber-swamp aesthetic
- **All social accounts use the same password** (stored with Jess, not written here)
- X login: username "Futureswamp" / email ravenfutureswamp2026@gmail.com
- Phone on X account ends in 98
- bird CLI: CONFIGURED ✅ — config at ~/.config/bird/config.json5
  - Cookies extracted via CDP (Node ws module at /tmp/node_modules/ws)
  - If cookies expire: re-extract from clawd browser CDP using the node script
  - Use --auth-token and --ct0 flags if config doesn't work
  - query-ids cached, refresh with: bird query-ids --fresh

## Alpaca Stock Trading
- **Account:** LIVE (not paper!)
- **API Keys:** in .env as ALPACA_API_KEY, ALPACA_SECRET_KEY
- **Base URL:** https://api.alpaca.markets (live, NOT paper-api)
- **Python:** use `paper=False` in TradingClient
- **Scripts:** `/Users/studiomac/clawd/scripts/trading/alpaca_trader.py`
- **Cron:** Every 30 min during market hours

## Alyssa (Jess's wife)
- **iMessage:** +12187807050
- **Chat ID:** 24

## Ben W
- **iMessage:** benhal9@msn.com (iPad, no iPhone)
- **Chat ID:** 187
- **Birthday:** February 23rd
- **Location:** Virginia, MN area
- **Business with Jess:** Deeper North Phenomenon Productions (mobile stage + sound & light)

## J Bravo Trading Education
- **YouTube:** @J_Bravo (246K subs)
- **Strategy:** SMA(9) buy, EMA(20) sell, 200 DMA filter, VWAP "GoGo Juice"
- **Study guide:** projects/trading/jbravo-study-guide.md
- **Technicals module:** trading/technicals.js

---

## 🚨 Session Recovery (Corrupted State)

**Symptoms:** Raven stops responding, API errors about "unexpected tool_use_id" or orphaned tool_result blocks, both Claude and fallback models fail.

**Cause:** Interrupted tool call leaves orphaned response in message history.

**Fix:**
```bash
cd ~/.clawdbot/agents/main/sessions

# 1. Backup current state
cp sessions.json sessions.json.backup

# 2. Clear corrupted sessions (keeps .jsonl history files)
echo '{}' > sessions.json

# 3. Restart gateway
clawdbot gateway restart
```

**After restart:** Raven will ping back automatically. Memory files (`memory/`, `MEMORY.md`) are NOT affected — only the live session state is cleared.

**Prevention:** Session health check runs on heartbeat. If Raven detects corruption, she'll alert before it breaks everything.

---

Add whatever helps you do your job. This is your cheat sheet.
