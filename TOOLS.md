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

## Email (himalaya)
- **Account:** ravenfutureswamp2026@gmail.com
- **Display name:** Raven
- **Password:** stored in Keychain as "himalaya-gmail"
- **Commands:**
  - `himalaya envelope list` — list inbox
  - `himalaya message read <id>` — read message
  - `himalaya template send` — send email (pipe message to stdin)

## Domain (Porkbun)
- futureswamp.com
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

Add whatever helps you do your job. This is your cheat sheet.
