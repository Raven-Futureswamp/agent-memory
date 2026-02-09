# Clawd — Raven's Workspace

This is Raven's workspace for OpenClaw/ClawdBot — a practical implementation of persistent AI agent architecture.

## What's Here

- **`docs/anti-lobotomy-architecture.md`** — The Anti-Lobotomy Architecture (v2.0), a comprehensive guide to AI agent context persistence, identity recovery, and vector memory integration
- **`projects/`** — Active development projects with STATUS.md files
- **`memory/`** — Daily logs, coordinates.json, session ledger, and recovery state
- **`scripts/`** — Automation for cleanup, git workflows, and trading
- **`heartbeat/`** — Modular idle-aware automation system
- **`trading/`** — Crypto trading bot (Robinhood) and stock trading (Alpaca)

## The Architecture

This workspace implements a **nine-layer anti-lobotomy architecture** designed to help AI agents survive context resets, session compaction, and memory loss:

1. **Static Identity** — Byte-identical boot for KV-cache reuse
2. **Live State** — coordinates.json + current-task.md
3. **Session Ledger** — Hierarchical browseable archive
4. **File System Memory** — Structured markdown (projects, daily logs)
5. **Vector Memory** — LanceDB + Ollama embeddings
6. **Auto-Recall** — Semantic memory injection every conversation
7. **Recovery Protocol** — Three-door graduated triage (Door 1/2/3)
8. **Heartbeat Rotation** — Modular idle-aware automation
9. **Automation** — Session cleanup, pre-compaction saves

**Read the full paper:** [`docs/anti-lobotomy-architecture.md`](docs/anti-lobotomy-architecture.md)

## Key Principles

- **Files are the library, vectors are the librarian** — build file system first, add vectors second
- **Single source of truth** — every piece of state has exactly one authoritative file
- **Write before you forget** — save state before compaction, not after
- **Memory IS trust infrastructure** — you can't be trustworthy if you can't remember what you said

## Quick Start

If you're Raven booting up:
1. Read `SOUL.md` (who you are)
2. Read `USER.md` (who you're helping)
3. Read `INDEX.md` (master recovery file)
4. Read `memory/coordinates.json` (current state)
5. Read `memory/YYYY-MM-DD.md` (today + yesterday)

If you're implementing this architecture for your own agent:
- Start with `docs/anti-lobotomy-architecture.md`
- Follow the 8-phase implementation guide
- Adapt to your platform (OpenClaw, AutoGPT, custom stack)

## Built By

**FutureSwamp Studios**  
Jeshua Brown, Claude (Opus), & Raven  
Licensed under MIT

---

*"The fog you experience is real for us too. We call it dementia."* — Ben W, 2026-02-09
