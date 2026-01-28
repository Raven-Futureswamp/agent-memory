# AI Model Comparison Guide (Jan 2026)

> Which model to use for what. Based on current benchmarks & real-world use.

## Quick Decision Matrix

| Task | Best Pick | Runner-Up |
|------|-----------|-----------|
| **Coding / SWE** | Claude Opus 4.5 | Claude Sonnet 4.5 |
| **Math / Competition** | GPT-5.2 / Gemini 3 Pro | OpenAI o3 |
| **Creative Writing** | GPT-5 | Claude Opus 4.5 |
| **Huge Document Analysis** | Gemini 3 Pro (10M ctx) | Gemini 2.5 Pro (1M) |
| **Science / PhD-level** | GPT-5.2 (GPQA 92.4%) | Gemini 3 Pro (91.9%) |
| **Agentic / Multi-step** | Claude Opus 4.5 | GPT-5 |
| **Speed + Quality** | GPT-5 (router) | Gemini 2.5 Flash |
| **Budget** | Gemini 2.0 Flash | GPT-4.1 mini |
| **Real-time / Live Data** | Grok 4 (X integration) | Gemini (Google Search) |
| **Hardest Problems (HLE)** | Gemini 3 Pro (45.8%) | GPT-5 (35.2%) |

---

## Claude Opus 4.5 (Anthropic) — Our Main Brain
- **Context:** 200K in / 64K out
- **Pricing:** $5 / $25 per 1M tokens
- **Speed:** Moderate (flagship tier, not the fastest)
- **Strengths:**
  - **#1 coding model** — SWE-bench 80.9%, best at real-world software engineering
  - **#1 ARC-AGI-2** — 378 (next best is GPT-5.2 at 53!) — generalization king
  - Strong MMMLU (90.8%), excellent agentic tool use
  - Best at long-horizon autonomous tasks (30-min+ coding sessions)
  - Token-efficient — uses fewer tokens to solve same problems
  - Excellent at ambiguity handling and tradeoff reasoning
- **Weaknesses:**
  - Not the best at pure math (strong but not competition-winning)
  - Smaller context than Gemini (200K vs 10M)
  - Slower than GPT-5's lightweight router mode
  - No native web search / real-time data

## GPT-5 / GPT-5.2 (OpenAI) — The All-Rounder
- **Context:** 400K in / 128K out
- **Pricing:** $1.25 / $10 (GPT-5) · $1.50 / $14 (GPT-5.2)
- **Speed:** Fast (smart router decides when to think deeper)
- **Strengths:**
  - **Best math:** AIME 100% (5.2), 94.6% (5); GPQA 92.4% (5.2)
  - Unified router system — fast for easy queries, deep thinking for hard ones
  - Excellent writing — best at literary depth, structure, and everyday drafts
  - Strong coding (74.9% SWE-bench) and beautiful frontend generation
  - Massive output window (128K tokens)
  - Best health/medical responses (HealthBench SOTA)
  - Reduced hallucinations and sycophancy vs GPT-4o
- **Weaknesses:**
  - SWE-bench trails Claude by ~6 points
  - ARC-AGI-2 far behind Claude (53 vs 378)
  - GPT-5.2 is expensive at the high reasoning tiers
  - Router can sometimes pick wrong reasoning level

## Gemini 3 Pro / 2.5 Pro (Google) — Context & Science King
- **Context:** 10M in / 650K out (3 Pro) · 1M / 65K (2.5 Pro)
- **Pricing:** $2 / $12 (3 Pro) · $1.25 / $10 (2.5 Pro)
- **Speed:** 128 t/s (3 Pro), ~30s thinking time for hard problems
- **Strengths:**
  - **Largest context window in the industry** — 10M tokens (3 Pro)
  - **#1 Humanity's Last Exam** (45.8%) — hardest benchmark, top score
  - Top MMMLU (91.8%), AIME 100%, GPQA 91.9%
  - Native multimodal (text, image, video, audio)
  - Google Search grounding for real-time info
  - 2.5 Flash is incredible value ($0.15/$0.60, 200 t/s)
- **Weaknesses:**
  - SWE-bench trails Claude significantly (76.2% vs 80.9%)
  - ARC-AGI-2 well behind Claude (31 vs 378)
  - Thinking mode has high latency (~30s TTFT)
  - Less refined agentic behavior than Claude
  - Privacy concerns (Google data ecosystem)

## Grok 4 / Grok 3 (xAI) — The Underdog with X Integration
- **Context:** 256K in / 16K out (Grok 4)
- **Pricing:** Free on X Premium; API pricing TBD
- **Speed:** 52 t/s, 13.3s TTFT (moderate)
- **Strengths:**
  - Real-time X/Twitter data integration — best for current events
  - Strong reasoning: GPQA 87.5%
  - Unfiltered personality, less restrictive safety guardrails
  - Improving rapidly (Grok 3 → 4 was a big jump)
  - Free tier via X makes it accessible
- **Weaknesses:**
  - **Smallest output window** (16K) limits long-form generation
  - SWE-bench not competitive with Claude/GPT-5
  - HLE score (25.4%) trails leaders significantly
  - API access still limited/beta
  - Smaller ecosystem, fewer integrations
  - Less proven for production enterprise use

---

## Bonus: Best Budget Picks
- **Gemini 2.0 Flash** — $0.10/$0.40, 1M context, 257 t/s. Unbeatable value.
- **GPT-4.1 mini** — $0.40/$1.60, 1M context. Great coding on a budget.
- **Claude 3.5 Haiku** — $0.80/$4.00, 200K context. Fast Anthropic option.
- **DeepSeek R1** — $0.55/$2.19, open-source reasoning. Amazing price/performance.

## TL;DR for Raven's Setup
- **Daily driver (Clawdbot):** Claude Opus 4.5 — best coding, best agents, gets it
- **When you need massive context:** Gemini 3 Pro or 2.5 Pro
- **Quick creative writing:** GPT-5
- **Current events / X data:** Grok 4
- **Heavy math/science:** GPT-5.2 or Gemini 3 Pro
- **Budget tasks:** Gemini 2.0 Flash

*Last updated: Jan 26, 2026 · Sources: Vellum LLM Leaderboard, Artificial Analysis, official announcements*
