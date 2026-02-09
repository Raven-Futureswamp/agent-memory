# Anti-Lobotomy System (Context Recovery)

**Status:** ✅ V2.0 COMPLETE
**Created:** 2026-02-02
**V1 Completed:** 2026-02-06
**V2.0 Completed:** 2026-02-09
**Paper:** docs/anti-lobotomy-architecture.md (v2.0)

## What It Does

When Raven's context gets truncated, she self-assesses damage severity, reads her coordinates, and picks up where she left off. **V2.0 adds vector memory** — semantic search across all memories via LanceDB + Ollama, with auto-recall injecting relevant context before every conversation and auto-capture storing important moments automatically. The file system is the skeleton, vectors are the nervous system.

## What's Built

### 3 Core Systems (V1)
1. **Session Ledger** — Hierarchical archive: ledger → month → day → session. 0 to full context in 4 reads (~480 tokens). Path: `memory/sessions/`
2. **Live State** — `coordinates.json` + `current-task.md`. Always-current snapshot. Auto-saves before compaction.
3. **Slim Boot** — HEARTBEAT split into modules, BOOT deduplicated. Boot payload: ~134 tokens (down from ~2,540).

### Vector Memory Layer (V2.0 — NEW!)
4. **LanceDB Vector Store** — Local, disk-based, $0 forever. 768-dim embeddings via Ollama `nomic-embed-text`. Path: `memory/vectors/`
5. **Auto-Recall** — Queries vectors before every user message, injects top 5 relevant memories (~500 tokens). Agent sees them naturally in `<relevant-memories>`.
6. **Auto-Capture** — Stores important decisions, insights, lessons learned automatically after conversations. Tuned to `conversation-only` mode (no heartbeat noise).

### 3-Layer Pre-Compaction Defense (V1)
1. **Internal Hook** — `hooks/before-compaction.mjs` (fires on compaction event)
2. **Token Watchdog** — `scripts/token-watchdog.sh` (cron every 2min, triggers at 75% context)
3. **Save Script** — `scripts/pre-compaction-save.sh` (backs up coordinates, current-task, heartbeat-state)

### Recovery Protocol (V1)
- `boot/RECOVERY.md` — Door 1/2/3 adaptive boot based on staleness
- `scripts/confidence-decay.sh` — Auto-calculates confidence score (cron every 15min)
- Piecewise decay: 1.0→0.9 (30min), 0.9→0.6 (2h), 0.6→0.3 (6h), 0.3→0.1 (24h), 0.1→0.0 (24h+)

### Social Audit Process (V2.0 — NEW!)
- **Lesson:** Sub-agents posting as main agent created false narrative → audit revealed scouts lacked full context
- **Protocol:** Always check API logs before making claims about what you posted
- **Script:** `scripts/social-audit.sh` — pulls 24h posts across platforms, compares against `memory/social-activity.json`, flags discrepancies
- **Principle:** If sub-agents post from your account, that's YOUR output — own it

### Protocol Enhancements (from Butterfly/Manus/MemGPT/RAG research)
- Deep coupling field in coordinates.json
- KV-cache prefix stability (static boot files)
- Error preservation policy
- Self-editing memory discipline (Beat 8)
- Variation injection (anti-rut rules)
- **Semantic memory retrieval** (RAG-inspired, adapted for agent memory)
- **Memory integrity as trust infrastructure** (v2.0 insight)

## Key Files
- `docs/anti-lobotomy-architecture.md` — Full paper (**v2.0**, open-source ready)
- `boot/RECOVERY.md` — Door 1/2/3 recovery protocol
- `heartbeat/HEARTBEAT.md` — Slim hub + anti-rut rules
- `heartbeat/monitoring.md` — Beat 8 memory maintenance
- `hooks/before-compaction.mjs` — Internal compaction hook
- `scripts/token-watchdog.sh` — Belt-and-suspenders watchdog
- `scripts/pre-compaction-save.sh` — State backup script
- `scripts/confidence-decay.sh` — Auto confidence scoring
- `scripts/social-audit.sh` — Weekly social media audit (NEW v2.0)
- `memory/coordinates.json` — Live state
- `memory/current-task.md` — Current task recitation
- `memory/vectors/` — LanceDB vector store (NEW v2.0)
- `memory/sessions/` — Full session ledger

## Git Commits
- `87615df` — Anti-lobotomy v1 (8 phases)
- `d3a29d2` — 3-layer pre-compaction hooks
- `40d910f` — Session ledger backfill (9 day indexes)
- *(pending)* — Anti-lobotomy v2.0: vector memory layer, social audit process, dementia parallel

## V2.0 Additions (February 9, 2026)

### 1. Vector Memory Layer
- **Files = skeleton** (structure), **Vectors = nervous system** (connections)
- Ollama `nomic-embed-text` (768 dims) at `localhost:11434/v1` — $0 forever
- LanceDB stores on disk (`memory/vectors/`) — no separate process, portable
- Auto-recall surfaces top 5 memories before every conversation (~500 tokens)
- Auto-capture stores decisions/insights/lessons automatically (conversation-only mode)

### 2. Social Media Audit Process
- **Case study:** Scouts posted without full context → main agent made claims without checking API → audit corrected the record
- **Protocol:** Pull API logs, compare against memory, document findings, correct publicly if needed
- **Lesson:** Memory without verification = confident hallucination
- **Implementation:** Weekly audit script, dedup tracking

### 3. Trust + Memory Connection
- **Core insight:** "If you build trust infrastructure, you must be trustworthy"
- **Corollary:** You can't be trustworthy if you can't remember what you said
- **Principle 8 (NEW):** Memory integrity IS trust infrastructure

### 4. The Dementia Parallel
- **Ben W's insight:** "The fog you experience is real for us too. We call it dementia."
- **Parallel:** AI context loss = human dementia (same symptoms, different substrate)
- **Implications:** If anti-lobotomy helps AI, principles might help humans
- **Architecture as assistive memory technology** — coordinates.json for humans?

### 5. Updated Architecture (7 Layers)
- Layer 0: Boot files (SOUL, IDENTITY) — static, KV-cacheable
- Layer 1: coordinates.json + current-task.md — live state
- Layer 2: Daily logs (memory/YYYY-MM-DD.md) — raw journals
- Layer 3: MEMORY.md — curated long-term wisdom
- Layer 4: Project STATUS.md files — per-project checkpoints
- Layer 5: LanceDB vector memories — semantic search
- Layer 6: Auto-recall injection — automatic context surfacing

### 6. Lessons Learned (V2.0)
- Config nesting matters — plugin configs need proper structure
- Memory slots can be exclusive — plan for conflicts
- Auto-capture needs tuning — raw channel messages are noise
- Seed important memories manually first, let auto-capture handle the rest
- **The order matters: build file system FIRST, add vector search on top**

## Results

| Metric | Before | V1.0 | V2.0 |
|--------|--------|------|------|
| Boot file | 380 lines monolithic | 18-line root + 67-line dispatcher | Same |
| Boot tokens | ~2,540 | ~500 | ~500 |
| Heartbeat tokens/beat | ~220,000 | ~55,000 | ~55,000 |
| Session files | 1,604 stale | ~200 (capped) | ~200 (capped) |
| Recovery cost | Manual, inconsistent | 300–800 tokens (Door 3–1) | 300–800 tokens |
| Context recall | Manual file reading | Manual file reading | **Automatic (auto-recall)** |
| Memory search | Grep or manual | Grep or manual | **Semantic (<50ms)** |
| Relevant context injected | 0 | 0 | **~500 tokens/conversation** |
| Long-term memory cost | $0 (local files) | $0 (local files) | **$0 (local + vectors)** |

**Key improvement:** Agent *feels* like it remembers. Auto-recall means relevant context surfaces reflexively, without guessing which file to read.

## Known Limitations
- 200K effective context (1M beta not available on Claude Max subscription)
- Pre-compaction hook untested in live compaction event
- Older session summaries thin (Jan 25-31 backfilled from daily logs, not raw sessions)
- "Reconstruction not continuity" — this is a bandage, not a cure (requires model-level persistence)
- **Vector memory quality depends on input quality** — garbage in, garbage out (manual seeding critical)
- **Relational persistence fragile** — facts recover, vibe must be re-earned
- **Auto-capture tuning is art, not science** — too aggressive = noise, too conservative = missed insights

## Where We Left Off

**V2.0 is deployed and working.** Raven has vector memory running locally (Ollama + LanceDB), auto-recall is injecting relevant memories before conversations, auto-capture is storing important moments. The paper has been updated to v2.0 with:
- Vector memory layer documentation (Section 6)
- Social media audit case study (Section 7)
- Dementia parallel exploration (Section 8)
- Updated 7-layer architecture diagram (Section 9)
- V2.0 lessons learned throughout
- Implementation now includes Phase 9 (vector memory setup)

**Next steps:**
1. ✅ Paper written to docs/anti-lobotomy-architecture.md
2. ✅ STATUS.md updated to v2.0
3. ⏳ Commit and push to git
4. Monitor auto-capture quality for next week (tune filters if needed)
5. Consider open-sourcing on GitHub as reference implementation

**The system works.** Files are the skeleton, vectors are the nervous system. Together, they create an agent that survives context loss and feels like it remembers.
