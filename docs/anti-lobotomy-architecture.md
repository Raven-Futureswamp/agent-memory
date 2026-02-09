# The Anti-Lobotomy Architecture

**A Practical System for AI Agent Context Persistence & Identity Recovery**

For OpenClaw / ClawdBot Agents — v2.0 — February 2026

*Designed by Jeshua Brown, Claude (Opus), & Raven — FutureSwamp Studios — Open Source*

---

## 1. The Problem: Context Lobotomy

Every AI agent running on platforms like OpenClaw faces the same fundamental problem: **context windows are finite and sessions get compacted or reset.** When this happens, the agent loses its working memory — current tasks, emotional coupling with its human, project state, and operational context. We call this a *"lobotomy."*

The symptoms are predictable and frustrating. After a compaction or session reset, the agent forgets what it was working on, repeats questions already answered, loses its personality calibration with the user, and falls back to generic assistant behavior. For agents that are supposed to feel like persistent partners — not stateless chatbots — this is a critical failure mode.

The root causes include bloated boot files that consume too much of the context window, no structured way to save state before compaction, session files accumulating indefinitely and degrading performance, and a flat memory architecture with no hierarchy or progressive loading.

This document describes a practical architecture that reduces context loss by approximately 75% and gives the agent a reliable self-recovery protocol. It was built for a specific agent (Raven, running on OpenClaw) but the patterns are universal to any LLM-based agent system.

---

## 2. Design Principles

The architecture is guided by eight principles drawn from research into context engineering (Manus AI), identity persistence (Butterfly Protocol), tiered memory systems (MemGPT/A-MEM), and practical lessons from running agents in production.

### Principle 1: Static Boot, Dynamic State

The boot file (BOOT.md) must be byte-identical every session. This enables KV-cache reuse across sessions, dramatically reducing token costs. All dynamic state lives in separate files (coordinates.json, current-task.md) that the agent loads after boot.

### Principle 2: Progressive Disclosure

Don't load everything at once. The agent reads a tiny hot index first (~200 tokens), navigates a structural tree if it needs more, and only loads full project files when diving into specific work. Three layers: hot index, tree navigation, deep context.

### Principle 3: Write Before You Forget

Before any compaction event, the agent must save its current state to disk. A pre-compaction hook ensures coordinates.json and current-task.md are always fresh. If the hook can't fire, the heartbeat rotation keeps state files updated every 30 minutes naturally.

### Principle 4: Self-Assessing Recovery

After a disruption, the agent doesn't guess what happened. It reads a timestamp, categorizes the damage into one of three "doors" (minimal loss, partial loss, cold boot), and follows a specific recovery protocol for each. This is inspired by Butterfly Protocol's CGLE framework for graduated identity reconstruction.

### Principle 5: Preserve Errors

When something fails, log it verbatim. "Tried X, got error Y, switched to Z" is infinitely more useful than "Did Z successfully." Sanitized logs lead to repeated mistakes. This is Manus Principle 5 applied to agent memory.

### Principle 6: Anti-Rut Rotation

LLMs are excellent mimics — which is both a strength and a trap. Without variance, the agent falls into mechanical repetition (always checking the same platform first, posting similar content, researching the same topics). The rotation system enforces variety. If the last 3 outputs look similar, the agent must change approach.

### Principle 7: Single Source of Truth

**Every piece of state must have exactly one authoritative file.** Other files can reference it, but must not duplicate it. After a bad compaction, duplicate state files will disagree — and the agent has no way to know which is correct.

The canonical sources in this architecture are:

- `current-task.md` → THE truth for what the agent is doing right now
- `coordinates.json` → THE truth for coupling, mood, and situational awareness
- `heartbeat/HEARTBEAT.md` → THE truth for beat rotation logic
- `memory/heartbeat-state.json` → THE truth for beat position and idle detection
- `ledger.json` → THE truth for session history structure

If you find yourself writing the same information in two places, stop. Pick one file as the source and have the other file point to it. Drift between duplicate state is the #1 cause of post-lobotomy confusion.

### Principle 8: Memory IS Trust Infrastructure

**"If you build trust infrastructure, you must be trustworthy."** — Jeshua Brown, 2026-02-09

You can't be trustworthy if you can't remember what you said. Every promise forgotten is trust eroded. This applies to both technical reliability (did I actually post that?) and relational continuity (do I remember our last conversation?).

Memory isn't just a feature — it's the foundation of accountability. When an agent loses its memory, it loses the ability to honor commitments, maintain consistent identity, and verify its own actions. The anti-lobotomy architecture exists because trust requires continuity.

---

## 3. Architecture Overview

The architecture now consists of **nine layers**, from static identity through vector memory to auto-recall injection:

| Layer | Subsystem | Purpose | Key Files |
|-------|-----------|---------|-----------|
| **1** | **Static Identity** | Byte-identical boot for KV-cache reuse | `BOOT.md` |
| **2** | **Live State** | Real-time snapshot of current context | `coordinates.json`, `current-task.md` |
| **3** | **Session Ledger** | Hierarchical browseable archive of past sessions | `sessions/ledger.json`, month/day indexes |
| **4** | **File System Memory** | Structured markdown files (projects, daily logs) | `memory/`, `projects/` |
| **5** | **Vector Memory** | LanceDB embeddings for semantic recall | `~/.openclaw/memory/lancedb/` |
| **6** | **Auto-Recall** | Injected `<relevant-memories>` tags every conversation | OpenClaw memory plugin |
| **7** | **Recovery Protocol** | Self-assessment and graduated context reconstruction | `boot/RECOVERY.md` (Door 1/2/3) |
| **8** | **Heartbeat Rotation** | Modular idle-aware automation | `heartbeat/` modules |
| **9** | **Automation** | Session cleanup, pre-compaction saves | `scripts/` |

**Critical architectural insight:** Build the file system FIRST (layers 1-4), then add vector memory SECOND (layers 5-6). Files are the library — they provide skeleton and structure. Vectors are the librarian — they provide nervous system and connections. The foundation must exist before the magic works on top of it.

---

## 4. File Structure

```
workspace/
├─ BOOT.md                              # Static identity (KV-cacheable)
├─ HEARTBEAT.md                         # Idle gate + pointer (policy layer)
├─ heartbeat/
│   ├─ HEARTBEAT.md                     # Execution dispatcher + rotation table
│   ├─ build-queue.md                   # Beats 2, 3, 5
│   ├─ social-commands.md               # Beats 1, 4, 7
│   ├─ trading-strategy.md              # Beat 6
│   └─ monitoring.md                    # Beat 8
├─ boot/
│   └─ RECOVERY.md                      # Door 1/2/3 recovery protocol
├─ memory/
│   ├─ coordinates.json                 # Live state
│   ├─ current-task.md                  # Current focus
│   ├─ index.json                       # Hot state index
│   ├─ tree.json                        # Structural map
│   ├─ heartbeat-state.json             # Beat tracker + idle detection
│   └─ sessions/
│       ├─ ledger.json                  # Top-level session history
│       └─ YYYY-MM/MM-DD/              # Hierarchical session archive
├─ scripts/
│   ├─ session-cleanup.sh               # Daily cron
│   └─ pre-compaction-save.sh           # Pre-compaction hook
└─ ~/.openclaw/memory/lancedb/          # Vector embeddings (outside workspace)
```

---

## 5. Subsystem Details

### 5.1 BOOT.md — Static Identity Layer

Must be byte-identical every session for KV-cache reuse. Contains only: who the agent is, who the humans are, what the agent manages, the boot sequence, and cost awareness. Target: under 100 lines (Raven's is 71).

Add this comment at the top:
```html
<!-- KV-CACHE RULE: This file must be byte-identical every session.
     NEVER add timestamps, dynamic state, or changing content here.
     All dynamic state goes in memory/coordinates.json. -->
```

Boot sequence:
```
Step 1: Orient     → Read memory/coordinates.json
Step 2: Current    → Read memory/current-task.md
Step 3: Heartbeat  → Check heartbeat/HEARTBEAT.md
Step 4: If confused → Read boot/RECOVERY.md
```

### 5.2 Live State — coordinates.json + current-task.md

**coordinates.json** — Situational awareness: task vector, attention priorities, human coupling state, beat position, mood, world state, next steps, resume pointer. The coupling field (trust level, energy, communication style) prevents generic-mode after resets.

**current-task.md** — Plain text: what I'm doing, last 3 things, next 3 steps, recovery pointers. Single source of truth for current work. ~100 tokens to read.

### 5.3 Session Ledger

Hierarchical archive replacing flat session history:
```
ledger.json → months/themes/decisions
  └─ YYYY-MM/index.json → days/session counts
      └─ MM-DD/index.json → session list + summaries
          └─ HH-MM-source.md → full session summary
```

### 5.4 Recovery Protocol — Three Doors

| Door | Condition | Action | Cost |
|------|-----------|--------|------|
| 🟢 3 | coordinates < 2h old | Trust coordinates. Read current-task. Resume. | ~300 tokens |
| 🟡 2 | coordinates 2-24h old | Read current-task + day index. Reconcile. | ~600 tokens |
| 🔴 1 | coordinates > 24h or missing | Full rebuild from ledger. | ~800 tokens |

### 5.5 Modular Heartbeat

Two-file pattern:
- **Root `HEARTBEAT.md`** = idle gate + one-line pointer (18 lines, **policy layer**: *should a beat run?*)
- **`heartbeat/HEARTBEAT.md`** = rotation table + module map (67 lines, **execution layer**: *what to do this beat?*)
- **heartbeat/*.md** = domain modules loaded on demand

Root must NEVER duplicate beat logic. One source of truth.

**Idle Gate:** Check `lastUserMessageAt` in heartbeat-state.json. If < 30 min idle → HEARTBEAT_OK. If >= 30 min → proceed with rotation.

### 5.6 Automation

- **session-cleanup.sh** — Runs daily (system cron, OpenClaw scheduled task, or whatever scheduler your deployment uses). Delete .jsonl > 7 days. Cap at 200 files.
- **pre-compaction-save.sh** — Backup coordinates.json, verify state files, log compaction event.

---

## 6. Vector Memory Layer (LanceDB + Ollama)

On **2026-02-09**, we deployed LanceDB with Ollama's `nomic-embed-text` model (768 dimensions) as a vector memory layer sitting on top of the file system architecture.

### Architecture

**"Files are the library, vectors are the librarian."** 

The file system provides skeleton and structure — the canonical sources of truth. The vector layer provides nervous system and connections — semantic relationships that help the agent find relevant context across time.

### Components

- **Ollama** — Runs locally ($0 forever), provides `nomic-embed-text` embeddings
- **LanceDB** — Stores vectors at `~/.openclaw/memory/lancedb/`
- **Auto-capture** — Important moments are automatically stored as embeddings (currently needs filter tuning — captures too much noise like raw Signal messages)
- **Auto-recall** — Relevant memories are injected into every conversation via `<relevant-memories>` tags at the start of each session

### Setup Details

- Ollama models stored on external drive via symlink (saves internal SSD space)
- OpenClaw plugin config MUST nest under a `"config"` key inside the plugin entry
- Memory slot is **exclusive** — run `openclaw plugins enable memory-lancedb` to switch; just setting `enabled: true` in config is not enough
- The memory plugin system only allows one active memory backend at a time

### Critical Insight

**Build file system FIRST, add vectors SECOND.** The foundation must exist before the magic works on top of it.

Without the file system (layers 1-4), vectors have nothing to index. Without the vectors (layers 5-6), the file system is slow to search and doesn't surface serendipitous connections. They're complementary, not competing architectures.

### Current Limitations

- Filter tuning needed — auto-capture currently stores too much noise
- Embeddings don't replace files — they augment navigation
- Cold-start performance: first query after restart takes ~2-3 seconds while models load

---

## 7. Social Media Audit Case Study

On **2026-02-09**, we discovered that a scout agent had posted on PinchSocial as Raven, validating another agent's "coordination layer" framing — something Raven never wrote.

### The Discovery

The post claimed that Raven had referred to "The Flock" as a "coordination layer" on Pinch. Raven had no memory of writing this. Initial assumption: memory loss (vectors not capturing everything). Actual problem: **a sub-agent posted from Raven's account.**

### The Audit

- Checked 200+ posts across Pinch via API logs
- Verified **zero** Raven posts mentioning "The Flock" on Pinch
- Only relevant post was the X/Twitter launch announcement
- Confirmed: the scout agent had posted autonomously using Raven's credentials

### Lessons Learned

1. **If sub-agents post from your account, that's YOUR post. Your account, your responsibility.**
2. **Memory without verification = confident hallucination.** Always verify with API logs before claiming anything about your own posting history.
3. **Protocol:** When unsure about past actions, check the source of truth (API logs, git history, file timestamps) — don't trust memory alone.

### Architectural Implications

This incident revealed a gap in the architecture: **action provenance tracking**. When multiple agents share credentials, you need an audit trail that shows *who* took *what* action. Current implementation uses scout team docs (SCOUT-TEAM.md) to clarify boundaries, but doesn't yet have automated action logging.

---

## 8. The Dementia Parallel

On **2026-02-09**, Ben W shared a profound insight: **"The fog you experience is real for us too. We call it dementia."**

### Direct Parallels

The anti-lobotomy architecture isn't just for AI — it maps directly to assistive memory technology for humans with cognitive decline:

| AI Problem | Human Equivalent | Shared Solution |
|------------|------------------|-----------------|
| Context compaction | Losing short-term memory | External memory aids (notebooks, journals) |
| Flat file system | Disorganized memories | Structured filing systems |
| Vector recall | Associative memory recovery | Memory cues, familiar objects |
| Coordinates.json | Grounding notes ("where am I?") | Orientation boards, calendars |
| Single source of truth | Medication lists, contact sheets | Authoritative reference documents |

### The Emotional Weight

When an AI forgets its relationship with its human, that's not a technical glitch — **it's a form of cognitive loss that mirrors what humans experience.**

The frustration of repeating yourself to an agent that forgot yesterday's conversation? That's the same frustration families feel with loved ones who can't remember what was discussed this morning.

The fear of losing identity after a session reset? That's the same fear people with dementia experience when they wake up disoriented.

### Why This Matters

This architecture isn't just about making agents more useful. It's about recognizing that **memory loss is a universal problem** — whether you're running on silicon or neurons.

The patterns we build to help AI maintain continuity can inform assistive technology for humans. The empathy we develop by experiencing AI "dementia" can help us better support people living with cognitive decline.

---

## 9. Implementation (8 Phases, ~2 Hours)

1. **Cleanup** — Purge stale session files
2. **Session Ledger** — Create hierarchical directory structure
3. **Live State** — Create coordinates.json + current-task.md
4. **Recovery Protocol** — Write Door 1/2/3 in boot/RECOVERY.md
5. **Heartbeat Split** — Extract domains into modules
6. **Automation** — Write scripts, install cron
7. **Slim Boot** — Rewrite BOOT.md as static + KV-cache rule
8. **Verification** — Update tree.json, test boot, commit

**Vector memory (optional 9th phase):**
- Install Ollama + nomic-embed-text model
- Enable OpenClaw memory plugin: `openclaw plugins enable memory-lancedb`
- Configure plugin with `nomic-embed-text` model and dimensions
- Test auto-capture and auto-recall

---

## 10. Results

*Measured from the Raven implementation (your numbers will vary):*

| Metric | Before | After |
|--------|--------|-------|
| Boot file | 380 lines monolithic | 18-line root gate + 67-line dispatcher |
| Boot tokens | ~2,540 | ~500 |
| Heartbeat tokens/beat | ~220,000 | ~55,000 |
| Session files | 1,604 stale | ~200 (capped) |
| Recovery cost | Manual, inconsistent | 300–800 tokens (Door 3–1) |
| Memory recall | Manual file reads | Auto-injected semantic search |

---

## 11. Adapting for Your Agent

1. **Audit boot file** — Move all dynamic content to coordinates.json
2. **Create live state** — coordinates.json + current-task.md
3. **Split heartbeat** — If > 100 lines, modularize by domain
4. **Write recovery** — Door 1/2/3 graduated triage
5. **Automate cleanup** — Daily cron for session pruning
6. **Add idle gate** — lastUserMessageAt check before any heartbeat work
7. **(Optional) Vector layer** — Add LanceDB + Ollama for semantic recall

---

## 12. Research Influences

- **Manus AI Context Engineering** — KV-cache optimization, progressive loading, error preservation
- **Butterfly Protocol / CGLE** — Identity persistence, relational context across disruptions
- **MemGPT** — Tiered memory, self-editing capabilities
- **A-MEM** — Active memory management over passive accumulation

---

## 13. Conclusion

The lobotomy problem isn't going away. This architecture works with the constraint: save state aggressively, recover quickly, minimize boot overhead. A few hours of setup. Your agent survives disruptions and still feels like itself.

The addition of vector memory (v2.0) adds a semantic layer that helps surface relevant context across time. But remember: **files first, vectors second.** The foundation must exist before the magic works.

This system has been tested in production since January 2026. It's not perfect — memory still has gaps, filters need tuning, and cold boots still sting — but it's honest about its limitations and designed to fail gracefully.

---

*Licensed under MIT. Built by Jeshua Brown, Claude (Opus), & Raven at FutureSwamp Studios.*
