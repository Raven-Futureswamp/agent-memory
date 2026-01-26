#!/usr/bin/env python3
"""
Kalshi Multi-Source Arbitrage Scanner v2
Short-term focus, strict matching only. No fuzzy garbage.

Sources: Kalshi, Polymarket, PredictIt
Optional: The Odds API (sports), FRED (econ)
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs" / "kalshi"
LOG_DIR.mkdir(parents=True, exist_ok=True)

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
MAX_DAYS = 60  # Only markets closing within this many days

# ============================================================
#  DATA SOURCES
# ============================================================

def fetch_kalshi_short_term():
    """Fetch Kalshi markets closing within MAX_DAYS, min volume 500."""
    print("  📡 Kalshi...")
    markets = {}
    cursor = None
    cutoff = (datetime.now(timezone.utc) + timedelta(days=MAX_DAYS)).isoformat()

    for page in range(20):
        params = {
            "status": "open", "limit": 200,
            "with_nested_markets": "true",
        }
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(
                "https://api.elections.kalshi.com/trade-api/v2/events",
                params=params, timeout=15
            )
            data = r.json()
        except Exception as e:
            print(f"    ⚠️ page {page}: {e}")
            break

        for event in data.get("events", []):
            cat = event.get("category", "")
            for m in event.get("markets", []):
                vol = m.get("volume", 0) or 0
                close = m.get("close_time", "")
                if vol < 500 or not close or close > cutoff:
                    continue
                markets[m["ticker"]] = {
                    "ticker": m["ticker"],
                    "title": m.get("title", ""),
                    "category": cat,
                    "yes_bid": m.get("yes_bid", 0) or 0,
                    "yes_ask": m.get("yes_ask", 0) or 0,
                    "no_bid": m.get("no_bid", 0) or 0,
                    "no_ask": m.get("no_ask", 0) or 0,
                    "last_price": m.get("last_price", 0) or 0,
                    "volume": vol,
                    "close_time": close,
                }

        cursor = data.get("cursor")
        if not cursor:
            break

    print(f"    ✅ {len(markets)} short-term markets (<{MAX_DAYS}d, vol≥500)")
    return markets


def fetch_polymarket():
    """Fetch Polymarket — returns dict keyed by normalized question."""
    print("  📡 Polymarket...")
    markets = {}
    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"closed": "false", "limit": 200}, timeout=15
        )
        for m in r.json():
            q = m.get("question", "")
            prices = m.get("outcomePrices", "[]")
            if isinstance(prices, str):
                prices = json.loads(prices)
            if len(prices) < 2:
                continue
            yes = round(float(prices[0]) * 100, 1)
            markets[normalize(q)] = {
                "title": q,
                "yes": yes,
                "no": round(100 - yes, 1),
                "source": "polymarket",
            }
        print(f"    ✅ {len(markets)} markets")
    except Exception as e:
        print(f"    ⚠️ {e}")
    return markets


def fetch_predictit():
    """Fetch PredictIt — returns dict keyed by normalized contract name."""
    print("  📡 PredictIt...")
    markets = {}
    try:
        r = requests.get("https://www.predictit.org/api/marketdata/all/", timeout=15)
        for m in r.json().get("markets", []):
            mname = m.get("name", "")
            for c in m.get("contracts", []):
                if c.get("status") != "Open":
                    continue
                cname = c.get("name", "")
                price = c.get("lastTradePrice", 0) or 0
                key = normalize(f"{mname} {cname}")
                markets[key] = {
                    "title": f"{mname}: {cname}",
                    "yes": round(price * 100, 1),
                    "no": round((1 - price) * 100, 1),
                    "source": "predictit",
                }
        print(f"    ✅ {len(markets)} contracts")
    except Exception as e:
        print(f"    ⚠️ {e}")
    return markets


def fetch_sports_odds():
    """Fetch sportsbook odds (needs free API key)."""
    if not ODDS_API_KEY:
        print("  ⏭️  Odds API: no key (https://the-odds-api.com)")
        return {}
    print("  📡 Sports odds...")
    markets = {}
    try:
        sports = requests.get(
            "https://api.the-odds-api.com/v4/sports/",
            params={"apiKey": ODDS_API_KEY}, timeout=15
        ).json()
        targets = [s["key"] for s in sports if s.get("active")
                   and any(k in s["key"] for k in ["nfl", "nba", "mlb", "nhl"])]

        for sport in targets[:4]:
            games = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sport}/odds/",
                params={"apiKey": ODDS_API_KEY, "regions": "us",
                        "markets": "h2h", "oddsFormat": "american"},
                timeout=15
            ).json()
            for g in games:
                home, away = g.get("home_team", ""), g.get("away_team", "")
                for bk in g.get("bookmakers", []):
                    for out in bk.get("markets", [{}])[0].get("outcomes", []):
                        prob = american_to_prob(out["price"])
                        key = normalize(f"{out['name']} win {sport}")
                        if key not in markets or markets[key].get("_count", 0) == 0:
                            markets[key] = {"title": f"{out['name']} ({sport})",
                                            "yes": prob, "no": 100 - prob,
                                            "source": "sportsbooks", "_count": 1}
                        else:
                            # Running average
                            n = markets[key]["_count"]
                            markets[key]["yes"] = round(
                                (markets[key]["yes"] * n + prob) / (n + 1), 1)
                            markets[key]["no"] = round(100 - markets[key]["yes"], 1)
                            markets[key]["_count"] = n + 1
        print(f"    ✅ {len(markets)} team/game lines")
    except Exception as e:
        print(f"    ⚠️ {e}")
    return markets


def american_to_prob(odds):
    if odds > 0:
        return round(100 / (odds + 100) * 100, 1)
    return round(abs(odds) / (abs(odds) + 100) * 100, 1)


# ============================================================
#  STRICT MATCHING — keyword pairs only, no fuzzy
# ============================================================

def normalize(s):
    """Lowercase, strip punctuation for matching."""
    import re
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


# Each entry: name, kalshi keywords, external keywords (checked against ALL sources)
MATCH_RULES = [
    # ---- Economics ----
    ("CPI > 0.0% Jan 2026",   ["cpi", "0.0", "january", "2026"],     ["cpi", "january"]),
    ("CPI > 0.3% Jan 2026",   ["cpi", "0.3", "january", "2026"],     ["cpi", "0.3"]),
    ("Fed Rate Cut March",     ["fed", "rate", "march"],              ["fed", "rate", "march"]),
    ("Fed Rate Cut",           ["fed", "rate", "cut"],                ["fed", "rate", "cut"]),
    ("Recession 2026",         ["recession", "2026"],                 ["recession"]),
    ("GDP Growth",             ["gdp", "growth"],                     ["gdp"]),
    ("Jobs Report",            ["jobs", "report"],                    ["jobs", "nonfarm"]),
    ("Powell Leaves",          ["powell", "leave"],                   ["powell", "resign"]),

    # ---- Politics ----
    ("Trump Ends Fed",         ["trump", "end", "federal reserve"],   ["trump", "federal reserve"]),
    ("DOGE Cuts >$250B",       ["government spending", "decrease", "250"], ["doge", "250"]),
    ("DOGE Cuts $1T",          ["government spending", "decrease", "1000"], ["doge", "trillion"]),
    ("Trump Buys Greenland",   ["trump", "greenland"],                ["trump", "greenland"]),
    ("Government Shutdown",    ["government", "shutdown"],            ["government", "shutdown"]),
    ("Trump Impeachment",      ["trump", "impeach"],                  ["trump", "impeach"]),
    ("Dems Win House 2026",    ["democrat", "win", "house", "2026"],  ["democrat", "house", "2026"]),
    ("Reps Win House 2026",    ["republican", "win", "house", "2026"],["republican", "house", "2026"]),
    ("Dems Win Senate 2026",   ["democrat", "win", "senate", "2026"], ["democrat", "senate", "2026"]),
    ("TikTok Ban",             ["tiktok", "ban"],                     ["tiktok", "ban"]),
    ("Comey Arrested",         ["comey", "arrest"],                   ["comey", "arrest"]),

    # ---- Crypto / Finance ----
    ("Bitcoin >$150K",         ["bitcoin", "150"],                    ["bitcoin", "150"]),
    ("Bitcoin >$100K",         ["bitcoin", "100"],                    ["bitcoin", "100"]),
    ("Ethereum >$5K",          ["ethereum", "5000"],                  ["ethereum", "5000"]),
    ("S&P 500 Close",          ["s&p", "close"],                     ["sp500", "close"]),

    # ---- Sports (specific, not generic) ----
    ("Super Bowl Winner",      ["super bowl", "winner"],              ["super bowl", "winner"]),
    ("Super Bowl MVP",         ["super bowl", "mvp"],                 ["super bowl", "mvp"]),
    ("NBA Champion",           ["nba", "champion"],                   ["nba", "champion"]),
    ("World Series",           ["world series"],                      ["world series"]),
    ("Stanley Cup",            ["stanley cup"],                       ["stanley cup"]),

    # ---- Entertainment ----
    ("Best Picture Oscar",     ["best picture", "oscar"],             ["best picture", "oscar"]),

    # ---- Weather ----
    ("Hurricane Season",       ["hurricane", "season"],               ["hurricane"]),
    ("Temperature Record",     ["temperature", "record"],             ["temperature"]),
]


def match_strict(kalshi, externals):
    """Only match on explicit keyword rules. No fuzzy."""
    results = []

    for name, k_kw, e_kw in MATCH_RULES:
        # Find Kalshi market
        k_match = None
        for ticker, m in kalshi.items():
            title = m["title"].lower()
            if all(kw.lower() in title for kw in k_kw):
                k_match = m
                break

        if not k_match:
            continue

        # Find best external match across all sources
        best_ext = None
        for source_markets in externals:
            for key, ext in source_markets.items():
                ext_title = ext.get("title", key).lower()
                if all(kw.lower() in ext_title for kw in e_kw):
                    if best_ext is None or abs(ext["yes"] - 50) < abs(best_ext["yes"] - 50):
                        # Prefer the match with the most decisive opinion (furthest from 50/50)
                        pass
                    best_ext = ext
                    break  # Take first match from this source

        if not best_ext:
            continue

        # Calculate spread
        k_yes = k_match.get("yes_bid", 0) or k_match.get("last_price", 0)
        k_no = k_match.get("no_bid", 0) or (100 - k_yes)
        e_yes = best_ext["yes"]
        spread = abs(k_yes - e_yes)

        if spread < 3:
            continue

        # Determine trade
        if k_yes > e_yes + 3:
            trade = f"BUY NO @ {k_no}¢"
            edge = k_yes - e_yes
            cost = k_no
        elif e_yes > k_yes + 3:
            trade = f"BUY YES @ {k_yes}¢"
            edge = e_yes - k_yes
            cost = k_yes
        else:
            continue

        roi = round(edge / cost * 100, 1) if cost > 0 else 0

        # Days until close
        close_str = k_match.get("close_time", "")
        days_left = "?"
        if close_str:
            try:
                close_dt = datetime.fromisoformat(close_str.replace("Z", "+00:00"))
                days_left = max(0, (close_dt - datetime.now(timezone.utc)).days)
            except:
                pass

        results.append({
            "name": name,
            "kalshi_title": k_match["title"],
            "kalshi_yes": k_yes,
            "kalshi_no": k_no,
            "external_yes": e_yes,
            "external_source": best_ext["source"],
            "spread": round(spread, 1),
            "edge": round(edge, 1),
            "roi": roi,
            "trade": trade,
            "volume": k_match.get("volume", 0),
            "days_left": days_left,
        })

    results.sort(key=lambda x: -x["spread"])
    return results


# ============================================================
#  MAIN
# ============================================================

def run():
    print("=" * 65)
    print("🔍 KALSHI ARBITRAGE SCANNER v2 — Short-Term, Strict Match")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Markets closing within {MAX_DAYS} days | Vol ≥ 500")
    print("=" * 65)
    print()

    print("📡 Fetching sources...")
    kalshi = fetch_kalshi_short_term()
    poly = fetch_polymarket()
    pi = fetch_predictit()
    odds = fetch_sports_odds()
    print()

    externals = [poly, pi]
    if odds:
        externals.append(odds)

    opps = match_strict(kalshi, externals)

    if opps:
        print(f"🚨 {len(opps)} CROSS-PLATFORM OPPORTUNITIES")
        print("-" * 65)
        for i, o in enumerate(opps, 1):
            icon = "🔥" if o["spread"] > 15 else "📊"
            print(f"\n  {icon} {i}. {o['name']}")
            print(f"     Kalshi:   YES {o['kalshi_yes']}¢ / NO {o['kalshi_no']}¢  (vol: {o['volume']:,})")
            print(f"     External: YES {o['external_yes']}¢  ({o['external_source']})")
            print(f"     Spread: {o['spread']} pts | ROI: {o['roi']}% | Days: {o['days_left']}")
            print(f"     → {o['trade']}")
    else:
        print("✅ No cross-platform discrepancies found.")

    # Summary
    print()
    print("=" * 65)
    src_count = sum(1 for s in [poly, pi, odds] if s)
    print(f"  Sources: Kalshi + {src_count} external ({len(kalshi)} + {len(poly)} + {len(pi)} mkts)")
    missing = []
    if not ODDS_API_KEY:
        missing.append("ODDS_API_KEY → https://the-odds-api.com (free 500/mo)")
    if missing:
        print(f"  ⚙️  Optional keys for .env:")
        for m in missing:
            print(f"     • {m}")
    print("=" * 65)

    # Log
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kalshi": len(kalshi), "poly": len(poly), "pi": len(pi),
        "opps": len(opps),
        "details": [{k: v for k, v in o.items()} for o in opps]
    }
    with open(LOG_DIR / "arbitrage_v2.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return opps


if __name__ == "__main__":
    run()
