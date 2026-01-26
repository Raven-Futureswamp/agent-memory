#!/usr/bin/env python3
"""
Kalshi Multi-Source Arbitrage Scanner v2.1
Short-term focus, strict matching only. No fuzzy garbage.

Sources: Kalshi, Polymarket, PredictIt
Optional: The Odds API (sports), FRED (econ)

v2.1 changes (Grok recommendations):
- CPI probability model using FRED historical data (12-month distribution)
- Catalyst calendar awareness (Fed meetings, CPI releases within 48h)
- Better sports odds: American → implied probability, flag >5% gaps
- Expanded keyword rules for CPI ranges, Fed decisions, weather, sports, GDP, unemployment
"""

import os
import sys
import json
import requests
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs" / "kalshi"
LOG_DIR.mkdir(parents=True, exist_ok=True)

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
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
    """Fetch sportsbook odds (needs free API key).
    v2.1: Average across ALL bookmakers for consensus probability.
    Flag any >5% gap vs Kalshi for arbitrage."""
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
                   and any(k in s["key"] for k in ["nfl", "nba", "mlb", "nhl", "mma"])]

        for sport in targets[:5]:
            resp = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sport}/odds/",
                params={"apiKey": ODDS_API_KEY, "regions": "us",
                        "markets": "h2h", "oddsFormat": "american"},
                timeout=15
            )
            if resp.status_code != 200:
                continue
            games = resp.json()
            if not isinstance(games, list):
                continue
            for g in games:
                home = g.get("home_team", "")
                away = g.get("away_team", "")
                game_time = g.get("commence_time", "")
                sport_key = sport.split("_")[-1] if "_" in sport else sport

                # Collect ALL bookmaker probabilities per outcome for consensus
                outcome_probs = {}  # {team_name: [prob1, prob2, ...]}
                for bk in g.get("bookmakers", []):
                    for mkt in bk.get("markets", []):
                        if mkt.get("key") != "h2h":
                            continue
                        for out in mkt.get("outcomes", []):
                            name = out.get("name", "")
                            price = out.get("price", 0)
                            if name and price:
                                prob = american_to_prob(price)
                                outcome_probs.setdefault(name, []).append(prob)

                for team_name, probs in outcome_probs.items():
                    if not probs:
                        continue
                    # Consensus: average across bookmakers
                    avg_prob = round(sum(probs) / len(probs), 1)
                    # Generate multiple key formats for matching
                    for key_fmt in [
                        normalize(f"{team_name} win {sport_key}"),
                        normalize(f"{team_name} {sport_key}"),
                        normalize(f"{team_name} win"),
                        normalize(f"{home} vs {away} {team_name}"),
                    ]:
                        markets[key_fmt] = {
                            "title": f"{team_name} win ({sport}: {away} @ {home})",
                            "yes": avg_prob,
                            "no": round(100 - avg_prob, 1),
                            "source": f"sportsbooks ({len(probs)} books)",
                            "books_count": len(probs),
                            "game_time": game_time,
                        }

        print(f"    ✅ {len(markets)} team/game lines (multi-book consensus)")
    except Exception as e:
        print(f"    ⚠️ {e}")
    return markets


def american_to_prob(odds):
    """Convert American odds to implied probability %.
    +150 → 40%, -200 → 66.7%, etc."""
    if odds > 0:
        return round(100 / (odds + 100) * 100, 1)
    return round(abs(odds) / (abs(odds) + 100) * 100, 1)


def fetch_fred_econ():
    """Fetch key economic data from FRED for CPI/Fed rate context.
    Now includes 12-month CPI history for probability distribution model."""
    if not FRED_API_KEY:
        print("  ⏭️  FRED: no key (https://fred.stlouisfed.org)")
        return {}
    print("  📡 FRED economic data...")
    data = {}
    series = {
        "DFEDTARU": "fed_rate_upper",      # Fed Funds upper target
        "DFEDTARL": "fed_rate_lower",      # Fed Funds lower target
        "CPIAUCSL": "cpi_level",           # CPI All Urban
        "UNRATE": "unemployment",          # Unemployment rate
        "GDP": "gdp",                      # GDP
    }
    for sid, label in series.items():
        try:
            # Fetch more observations for CPI to build distribution
            limit = 14 if sid == "CPIAUCSL" else 3
            r = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": sid, "api_key": FRED_API_KEY,
                        "file_type": "json", "limit": limit, "sort_order": "desc"},
                timeout=10
            )
            obs = r.json().get("observations", [])
            vals = [float(o["value"]) for o in obs if o.get("value", ".") != "."]
            if vals:
                data[label] = vals[0]
                if len(vals) >= 2 and label == "cpi_level":
                    data["cpi_mom"] = round((vals[0] - vals[1]) / vals[1] * 100, 3)
                    # Build 12-month CPI MoM distribution for probability model
                    if len(vals) >= 3:
                        cpi_mom_history = []
                        for i in range(len(vals) - 1):
                            mom = round((vals[i] - vals[i+1]) / vals[i+1] * 100, 3)
                            cpi_mom_history.append(mom)
                        data["cpi_mom_history"] = cpi_mom_history
                        data["cpi_mom_mean"] = round(statistics.mean(cpi_mom_history), 3)
                        data["cpi_mom_stdev"] = round(statistics.stdev(cpi_mom_history), 3) if len(cpi_mom_history) > 1 else 0.1
        except:
            pass

    # Fetch GDP growth rate (quarterly, annualized)
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": "A191RL1Q225SBEA", "api_key": FRED_API_KEY,
                    "file_type": "json", "limit": 4, "sort_order": "desc"},
            timeout=10
        )
        obs = r.json().get("observations", [])
        vals = [float(o["value"]) for o in obs if o.get("value", ".") != "."]
        if vals:
            data["gdp_growth"] = vals[0]
            if len(vals) >= 2:
                data["gdp_growth_history"] = vals
    except:
        pass

    if data:
        print(f"    ✅ Fed rate: {data.get('fed_rate_lower','?')}-{data.get('fed_rate_upper','?')}%")
        if "cpi_mom" in data:
            print(f"    ✅ CPI MoM: {data['cpi_mom']}% (mean: {data.get('cpi_mom_mean','?')}%, stdev: {data.get('cpi_mom_stdev','?')}%)")
        if "unemployment" in data:
            print(f"    ✅ Unemployment: {data['unemployment']}%")
        if "gdp_growth" in data:
            print(f"    ✅ GDP growth: {data['gdp_growth']}% (annualized)")
        if data.get("cpi_mom_history"):
            print(f"    📊 CPI MoM last {len(data['cpi_mom_history'])} months: {data['cpi_mom_history']}")
    return data


def build_cpi_probability_model(econ_data):
    """
    Build CPI probability model from FRED historical data.
    Uses last 12 months of CPI MoM to estimate probability of each threshold.
    Returns dict like {"cpi_gt_0.0": 92.3, "cpi_gt_0.1": 78.5, ...}
    """
    history = econ_data.get("cpi_mom_history", [])
    if not history:
        return {}

    mean = econ_data.get("cpi_mom_mean", 0.2)
    stdev = econ_data.get("cpi_mom_stdev", 0.1)

    thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    probs = {}

    for thresh in thresholds:
        # Empirical: count how many of last N months exceeded this threshold
        count_above = sum(1 for v in history if v > thresh)
        empirical_prob = count_above / len(history) * 100

        # Gaussian estimate (for smoother probabilities)
        if stdev > 0:
            from math import erf, sqrt
            z = (thresh - mean) / stdev
            gaussian_prob = (1 - 0.5 * (1 + erf(z / sqrt(2)))) * 100
        else:
            gaussian_prob = 100.0 if mean > thresh else 0.0

        # Blend: 60% empirical, 40% gaussian (empirical more trustworthy with limited data)
        blended = round(0.6 * empirical_prob + 0.4 * gaussian_prob, 1)
        probs[f"cpi_gt_{thresh}"] = blended

    return probs


def get_catalyst_calendar():
    """
    Return upcoming economic catalysts within 48 hours.
    Fed meetings and CPI release dates for 2025-2026.
    These are high-opportunity windows where markets move.
    """
    # Known Fed FOMC meeting dates (2025-2026)
    fed_meetings = [
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    ]

    # Known CPI release dates (2025-2026, typically 2nd week of month)
    cpi_releases = [
        "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10",
        "2025-05-13", "2025-06-11", "2025-07-11", "2025-08-12",
        "2025-09-10", "2025-10-14", "2025-11-12", "2025-12-10",
        "2026-01-14", "2026-02-11", "2026-03-11", "2026-04-14",
        "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12",
        "2026-09-10", "2026-10-13", "2026-11-10", "2026-12-09",
    ]

    # Jobs report dates (first Friday of month typically)
    jobs_releases = [
        "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02",
        "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05",
        "2025-10-03", "2025-11-07", "2025-12-05",
        "2026-01-09", "2026-02-06", "2026-03-06", "2026-04-03",
        "2026-05-01", "2026-06-05", "2026-07-02", "2026-08-07",
        "2026-09-04", "2026-10-02", "2026-11-06", "2026-12-04",
    ]

    now = datetime.now(timezone.utc)
    window = timedelta(hours=48)
    catalysts = []

    for date_str in fed_meetings:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=18)
            if 0 <= (dt - now).total_seconds() <= window.total_seconds():
                catalysts.append({"type": "FED_MEETING", "date": date_str,
                                  "note": f"⚡ Fed FOMC meeting {date_str} — high-opportunity window!"})
        except:
            pass

    for date_str in cpi_releases:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=13)
            if 0 <= (dt - now).total_seconds() <= window.total_seconds():
                catalysts.append({"type": "CPI_RELEASE", "date": date_str,
                                  "note": f"⚡ CPI data release {date_str} — high-opportunity window!"})
        except:
            pass

    for date_str in jobs_releases:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=13)
            if 0 <= (dt - now).total_seconds() <= window.total_seconds():
                catalysts.append({"type": "JOBS_REPORT", "date": date_str,
                                  "note": f"⚡ Jobs report {date_str} — high-opportunity window!"})
        except:
            pass

    return catalysts


# ============================================================
#  STRICT MATCHING — keyword pairs only, no fuzzy
# ============================================================

def normalize(s):
    """Lowercase, strip punctuation for matching."""
    import re
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


# Each entry: name, kalshi keywords, external keywords (checked against ALL sources)
MATCH_RULES = [
    # ---- CPI Monthly Ranges (Grok rec: specific thresholds) ----
    ("CPI > 0.0% Jan 2026",   ["cpi", "0.0", "january", "2026"],     ["cpi", "january"]),
    ("CPI > 0.1% Jan 2026",   ["cpi", "0.1", "january", "2026"],     ["cpi", "0.1"]),
    ("CPI > 0.2% Jan 2026",   ["cpi", "0.2", "january", "2026"],     ["cpi", "0.2"]),
    ("CPI > 0.3% Jan 2026",   ["cpi", "0.3", "january", "2026"],     ["cpi", "0.3"]),
    ("CPI > 0.4% Jan 2026",   ["cpi", "0.4", "january", "2026"],     ["cpi", "0.4"]),
    ("CPI > 0.0% Feb 2026",   ["cpi", "0.0", "february", "2026"],    ["cpi", "february"]),
    ("CPI > 0.1% Feb 2026",   ["cpi", "0.1", "february", "2026"],    ["cpi", "0.1"]),
    ("CPI > 0.2% Feb 2026",   ["cpi", "0.2", "february", "2026"],    ["cpi", "0.2"]),
    ("CPI > 0.3% Feb 2026",   ["cpi", "0.3", "february", "2026"],    ["cpi", "0.3"]),
    ("CPI > 0.4% Feb 2026",   ["cpi", "0.4", "february", "2026"],    ["cpi", "0.4"]),
    # Generic CPI (any month)
    ("CPI > 0.0%",            ["cpi", "0.0"],                        ["cpi", "inflation"]),
    ("CPI > 0.1%",            ["cpi", "0.1"],                        ["cpi", "inflation"]),
    ("CPI > 0.2%",            ["cpi", "0.2"],                        ["cpi", "inflation"]),
    ("CPI > 0.3%",            ["cpi", "0.3"],                        ["cpi", "inflation"]),
    ("CPI > 0.4%",            ["cpi", "0.4"],                        ["cpi", "inflation"]),
    ("CPI YoY",               ["cpi", "year"],                       ["cpi", "year"]),

    # ---- Fed Rate Decisions (Grok rec: hold/cut/hike) ----
    ("Fed Rate Cut March",     ["fed", "rate", "march"],              ["fed", "rate", "march"]),
    ("Fed Rate Cut",           ["fed", "rate", "cut"],                ["fed", "rate", "cut"]),
    ("Fed Rate Hold",          ["fed", "rate", "hold"],               ["fed", "rate", "hold"]),
    ("Fed Rate Hold Jan",      ["fed", "rate", "hold", "january"],    ["fed", "rate", "january"]),
    ("Fed Rate Hold Mar",      ["fed", "rate", "hold", "march"],      ["fed", "rate", "march"]),
    ("Fed Rate Hike",          ["fed", "rate", "hike"],               ["fed", "rate", "hike"]),
    ("Fed Rate Hike",          ["fed", "rate", "increase"],           ["fed", "rate", "increase"]),
    ("Fed Rate Cut June",      ["fed", "rate", "cut", "june"],        ["fed", "rate", "june"]),
    ("Fed Rate Decision",      ["federal funds", "rate"],             ["federal funds", "rate"]),
    ("Fed Rate Target",        ["fed", "target", "rate"],             ["fed", "target"]),

    # ---- Economics (expanded) ----
    ("Recession 2026",         ["recession", "2026"],                 ["recession"]),
    ("GDP Growth > 0%",        ["gdp", "growth", "0"],               ["gdp", "growth"]),
    ("GDP Growth > 1%",        ["gdp", "growth", "1"],               ["gdp", "growth"]),
    ("GDP Growth > 2%",        ["gdp", "growth", "2"],               ["gdp", "growth"]),
    ("GDP Growth > 3%",        ["gdp", "growth", "3"],               ["gdp", "growth"]),
    ("GDP Growth Q1",          ["gdp", "q1"],                        ["gdp", "quarter"]),
    ("GDP Growth Q2",          ["gdp", "q2"],                        ["gdp", "quarter"]),
    ("GDP Negative",           ["gdp", "negative"],                  ["gdp", "contraction"]),
    ("Jobs Report",            ["jobs", "report"],                    ["jobs", "nonfarm"]),
    ("Nonfarm Payrolls",       ["nonfarm", "payroll"],                ["nonfarm", "payroll"]),
    ("Unemployment > 4.0%",    ["unemployment", "4.0"],               ["unemployment"]),
    ("Unemployment > 4.5%",    ["unemployment", "4.5"],               ["unemployment"]),
    ("Unemployment > 5.0%",    ["unemployment", "5.0"],               ["unemployment"]),
    ("Unemployment Rate",      ["unemployment", "rate"],              ["unemployment", "rate"]),
    ("Jobless Claims",         ["jobless", "claims"],                 ["jobless", "claims"]),
    ("Powell Leaves",          ["powell", "leave"],                   ["powell", "resign"]),
    ("Inflation > 3%",         ["inflation", "3"],                    ["inflation"]),
    ("Inflation > 4%",         ["inflation", "4"],                    ["inflation"]),

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
    ("Tariffs",                ["tariff"],                            ["tariff"]),
    ("Debt Ceiling",           ["debt ceiling"],                      ["debt ceiling"]),

    # ---- Crypto / Finance ----
    ("Bitcoin >$150K",         ["bitcoin", "150"],                    ["bitcoin", "150"]),
    ("Bitcoin >$100K",         ["bitcoin", "100"],                    ["bitcoin", "100"]),
    ("Ethereum >$5K",          ["ethereum", "5000"],                  ["ethereum", "5000"]),
    ("S&P 500 Close",          ["s&p", "close"],                     ["sp500", "close"]),
    ("S&P 500 > 6000",         ["s&p", "6000"],                      ["sp500", "6000"]),

    # ---- NFL Teams (Grok rec: specific matchups) ----
    ("Chiefs Win",             ["chiefs", "win"],                     ["chiefs", "win"]),
    ("Eagles Win",             ["eagles", "win"],                     ["eagles", "win"]),
    ("Bills Win",              ["bills", "win"],                      ["bills", "win"]),
    ("49ers Win",              ["49ers", "win"],                      ["49ers", "win"]),
    ("Ravens Win",             ["ravens", "win"],                     ["ravens", "win"]),
    ("Lions Win",              ["lions", "win"],                      ["lions", "win"]),
    ("Cowboys Win",            ["cowboys", "win"],                    ["cowboys", "win"]),
    ("Packers Win",            ["packers", "win"],                    ["packers", "win"]),
    ("Bengals Win",            ["bengals", "win"],                    ["bengals", "win"]),
    ("Dolphins Win",           ["dolphins", "win"],                   ["dolphins", "win"]),
    ("Steelers Win",           ["steelers", "win"],                   ["steelers", "win"]),
    ("Vikings Win",            ["vikings", "win"],                    ["vikings", "win"]),
    ("Texans Win",             ["texans", "win"],                     ["texans", "win"]),
    ("Commanders Win",         ["commanders", "win"],                 ["commanders", "win"]),
    ("Super Bowl Winner",      ["super bowl", "winner"],              ["super bowl", "winner"]),
    ("Super Bowl MVP",         ["super bowl", "mvp"],                 ["super bowl", "mvp"]),

    # ---- NBA Teams (Grok rec: specific matchups) ----
    ("Celtics Win",            ["celtics", "win"],                    ["celtics", "win"]),
    ("Thunder Win",            ["thunder", "win"],                    ["thunder", "win"]),
    ("Nuggets Win",            ["nuggets", "win"],                    ["nuggets", "win"]),
    ("Lakers Win",             ["lakers", "win"],                     ["lakers", "win"]),
    ("Bucks Win",              ["bucks", "win"],                      ["bucks", "win"]),
    ("Warriors Win",           ["warriors", "win"],                   ["warriors", "win"]),
    ("Knicks Win",             ["knicks", "win"],                     ["knicks", "win"]),
    ("76ers Win",              ["76ers", "win"],                      ["76ers", "win"]),
    ("Cavaliers Win",          ["cavaliers", "win"],                  ["cavaliers", "win"]),
    ("Timberwolves Win",       ["timberwolves", "win"],               ["timberwolves", "win"]),
    ("NBA Champion",           ["nba", "champion"],                   ["nba", "champion"]),

    # ---- Other Sports ----
    ("World Series",           ["world series"],                      ["world series"]),
    ("Stanley Cup",            ["stanley cup"],                       ["stanley cup"]),
    ("MLB Winner",             ["mlb", "winner"],                     ["mlb", "winner"]),

    # ---- Entertainment ----
    ("Best Picture Oscar",     ["best picture", "oscar"],             ["best picture", "oscar"]),

    # ---- Weather (Grok rec: hurricane + temperature) ----
    ("Hurricane Season",       ["hurricane", "season"],               ["hurricane"]),
    ("Hurricane Category",     ["hurricane", "category"],             ["hurricane", "category"]),
    ("Named Storms",           ["named storm"],                       ["named storm"]),
    ("Major Hurricane",        ["major hurricane"],                   ["major hurricane"]),
    ("Atlantic Hurricane",     ["atlantic", "hurricane"],             ["atlantic", "hurricane"]),
    ("Temperature Record",     ["temperature", "record"],             ["temperature"]),
    ("Temperature Above",      ["temperature", "above"],              ["temperature", "above"]),
    ("Temperature NYC",        ["temperature", "new york"],           ["temperature", "new york"]),
    ("Temperature LA",         ["temperature", "los angeles"],        ["temperature", "los angeles"]),
    ("Temperature Chicago",    ["temperature", "chicago"],            ["temperature", "chicago"]),
    ("Heat Wave",              ["heat wave"],                         ["heat wave"]),
    ("Hottest Month",          ["hottest", "month"],                  ["hottest", "month"]),
    ("Coldest Day",            ["coldest", "day"],                    ["coldest"]),
    ("Snowfall Record",        ["snowfall", "record"],                ["snowfall"]),
    ("Tornado",                ["tornado"],                           ["tornado"]),
    ("Wildfire",               ["wildfire"],                          ["wildfire"]),
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
    print("🔍 KALSHI ARBITRAGE SCANNER v2.1 — Short-Term, Strict Match")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Markets closing within {MAX_DAYS} days | Vol ≥ 500")
    print("=" * 65)
    print()

    # Check catalyst calendar first
    print("📅 Checking catalyst calendar...")
    catalysts = get_catalyst_calendar()
    if catalysts:
        for c in catalysts:
            print(f"  {c['note']}")
    else:
        print("  No catalysts within 48 hours.")
    print()

    print("📡 Fetching sources...")
    kalshi = fetch_kalshi_short_term()
    poly = fetch_polymarket()
    pi = fetch_predictit()
    odds = fetch_sports_odds()
    econ = fetch_fred_econ()
    print()

    externals = [poly, pi]
    if odds:
        externals.append(odds)

    opps = match_strict(kalshi, externals)

    # === CPI PROBABILITY MODEL (Grok rec) ===
    cpi_model = {}
    if econ:
        cpi_model = build_cpi_probability_model(econ)
        if cpi_model:
            print("📊 CPI Probability Model (FRED-based):")
            for thresh_key, model_prob in sorted(cpi_model.items()):
                thresh = thresh_key.replace("cpi_gt_", ">")
                print(f"    CPI MoM {thresh}%: {model_prob:.1f}% probability (model)")

            # Compare CPI model vs Kalshi CPI market prices
            print()
            print("🔬 CPI Model vs Kalshi prices:")
            cpi_arb_found = False
            seen_cpi_tickers = set()  # Avoid duplicate matches
            for ticker, m in kalshi.items():
                title_lower = m["title"].lower()
                if "cpi" not in title_lower:
                    continue
                if ticker in seen_cpi_tickers:
                    continue
                for thresh_key, model_prob in cpi_model.items():
                    thresh_val = thresh_key.replace("cpi_gt_", "")
                    # More precise matching: look for the exact threshold with context
                    # e.g., "more than 0.2%" or "above 0.2%" — but NOT "-0.2%"
                    import re
                    # Match "more than X%" or "above X%" where X is our threshold (not negative)
                    pattern = rf'(?:more than|above|greater than|over)\s+{re.escape(thresh_val)}%'
                    if not re.search(pattern, title_lower):
                        continue
                    if ticker in seen_cpi_tickers:
                        break
                    seen_cpi_tickers.add(ticker)
                    kalshi_yes = m.get("yes_bid", 0) or m.get("last_price", 0)
                    if kalshi_yes <= 0:
                        continue
                    gap = abs(model_prob - kalshi_yes)
                    if gap <= 5:
                        continue
                    cpi_arb_found = True
                    direction = "UNDERPRICED" if model_prob > kalshi_yes else "OVERPRICED"
                    print(f"    ⚡ {m['title']}")
                    print(f"       Kalshi: {kalshi_yes}¢ | Model: {model_prob:.1f}% | Gap: {gap:.1f} pts → {direction}")
                    # Determine trade direction
                    if model_prob > kalshi_yes + 5:
                        trade = f"BUY YES @ {kalshi_yes}¢"
                        edge = model_prob - kalshi_yes
                        cost = kalshi_yes
                    elif kalshi_yes > model_prob + 5:
                        k_no = m.get("no_bid", 0) or (100 - kalshi_yes)
                        trade = f"BUY NO @ {k_no}¢"
                        edge = kalshi_yes - model_prob
                        cost = k_no
                    else:
                        continue
                    roi = round(edge / cost * 100, 1) if cost > 0 else 0
                    close_str = m.get("close_time", "")
                    days_left = "?"
                    if close_str:
                        try:
                            close_dt = datetime.fromisoformat(close_str.replace("Z", "+00:00"))
                            days_left = max(0, (close_dt - datetime.now(timezone.utc)).days)
                        except:
                            pass
                    opps.append({
                        "name": f"CPI Model: {m['title'][:50]}",
                        "kalshi_title": m["title"],
                        "kalshi_yes": kalshi_yes,
                        "kalshi_no": m.get("no_bid", 0) or (100 - kalshi_yes),
                        "external_yes": round(model_prob, 1),
                        "external_source": "FRED CPI model",
                        "spread": round(gap, 1),
                        "edge": round(edge, 1),
                        "roi": roi,
                        "trade": trade,
                        "volume": m.get("volume", 0),
                        "days_left": days_left,
                        "fred_note": f"Model: {model_prob:.1f}% (mean MoM: {econ.get('cpi_mom_mean','?')}%, stdev: {econ.get('cpi_mom_stdev','?')}%)",
                    })
                    break  # One model match per CPI market
            if not cpi_arb_found:
                print("    No CPI arbitrage opportunities (Kalshi aligned with model)")
            print()

    # Add FRED context to economic opportunities
    if econ:
        for opp in opps:
            name_lower = opp["name"].lower()
            if "cpi" in name_lower and "cpi_mom" in econ and not opp.get("fred_note"):
                opp["fred_note"] = f"Last CPI MoM: {econ['cpi_mom']}%"
            elif "fed" in name_lower and "fed_rate_upper" in econ:
                opp["fred_note"] = f"Current rate: {econ.get('fed_rate_lower','?')}-{econ['fed_rate_upper']}%"
            elif "recession" in name_lower and "unemployment" in econ:
                opp["fred_note"] = f"Unemployment: {econ['unemployment']}%"
            elif "gdp" in name_lower and "gdp_growth" in econ:
                opp["fred_note"] = f"Last GDP growth: {econ['gdp_growth']}% (annualized)"
            elif "unemployment" in name_lower and "unemployment" in econ:
                opp["fred_note"] = f"Current unemployment: {econ['unemployment']}%"

    # Add catalyst flags to relevant opportunities
    if catalysts:
        for opp in opps:
            name_lower = opp["name"].lower()
            for c in catalysts:
                if c["type"] == "FED_MEETING" and ("fed" in name_lower or "rate" in name_lower):
                    opp["catalyst_note"] = c["note"]
                elif c["type"] == "CPI_RELEASE" and ("cpi" in name_lower or "inflation" in name_lower):
                    opp["catalyst_note"] = c["note"]
                elif c["type"] == "JOBS_REPORT" and ("job" in name_lower or "unemployment" in name_lower or "nonfarm" in name_lower):
                    opp["catalyst_note"] = c["note"]

    # === SPORTS ODDS GAP DETECTION (Grok rec: flag >5% gap) ===
    if odds:
        print("🏈 Sports odds gap detection (>5% vs Kalshi):")
        sports_gaps_found = False
        # Only compare Kalshi markets that are actual game outcomes
        # (must contain "win" or "winner" — filter out prop bets, announcer markets, etc.)
        game_keywords = ["win", "winner", "beat", "defeat", "champion"]
        for ticker, m in kalshi.items():
            title_lower = m["title"].lower()
            if not any(gk in title_lower for gk in game_keywords):
                continue  # Skip non-game markets (prop bets, announcer markets, etc.)
            kalshi_yes = m.get("yes_bid", 0) or m.get("last_price", 0)
            if kalshi_yes <= 0:
                continue
            for odds_key, odds_data in odds.items():
                sports_prob = odds_data["yes"]
                gap = abs(sports_prob - kalshi_yes)
                # Match by team name overlap (need at least 2 meaningful words in common)
                odds_words = set(odds_key.split()) - {"win", "the", "to", "a", "in", "of", "at", "vs"}
                title_words = set(normalize(m["title"]).split()) - {"win", "the", "to", "a", "in", "of", "at", "vs", "will"}
                common = odds_words & title_words
                if len(common) >= 2 and gap > 5:
                    sports_gaps_found = True
                    direction = "Kalshi underpriced" if sports_prob > kalshi_yes else "Kalshi overpriced"
                    print(f"    ⚡ {m['title'][:60]}")
                    print(f"       Kalshi: {kalshi_yes}¢ | Sportsbooks: {sports_prob}% | Gap: {gap:.1f}% → {direction}")
                    books = odds_data.get("books_count", "?")
                    print(f"       Source: consensus of {books} bookmakers")
                    break  # One match per Kalshi market
        if not sports_gaps_found:
            print("    No significant sports gaps found (all <5%)")
        print()

    # Re-sort all opportunities by spread
    opps.sort(key=lambda x: -x["spread"])

    if opps:
        print(f"🚨 {len(opps)} OPPORTUNITIES FOUND")
        print("-" * 65)
        for i, o in enumerate(opps, 1):
            icon = "🔥" if o["spread"] > 15 else "📊"
            catalyst = " ⚡CATALYST" if o.get("catalyst_note") else ""
            model = " 🧮MODEL" if "model" in o.get("external_source", "").lower() else ""
            print(f"\n  {icon} {i}. {o['name']}{catalyst}{model}")
            print(f"     Kalshi:   YES {o['kalshi_yes']}¢ / NO {o['kalshi_no']}¢  (vol: {o['volume']:,})")
            print(f"     External: YES {o['external_yes']}¢  ({o['external_source']})")
            print(f"     Spread: {o['spread']} pts | ROI: {o['roi']}% | Days: {o['days_left']}")
            print(f"     → {o['trade']}")
            if o.get("fred_note"):
                print(f"     📈 FRED: {o['fred_note']}")
            if o.get("catalyst_note"):
                print(f"     ⚡ {o['catalyst_note']}")
    else:
        print("✅ No cross-platform discrepancies found.")

    # Summary
    print()
    print("=" * 65)
    src_count = sum(1 for s in [poly, pi, odds] if s)
    print(f"  Sources: Kalshi + {src_count} external ({len(kalshi)} + {len(poly)} + {len(pi)} mkts)")
    if econ:
        print(f"  📈 FRED: Rate {econ.get('fed_rate_lower','?')}-{econ.get('fed_rate_upper','?')}% | CPI MoM {econ.get('cpi_mom','?')}% | Unemp {econ.get('unemployment','?')}%")
        if "gdp_growth" in econ:
            print(f"  📈 GDP: {econ['gdp_growth']}% (annualized)")
    if cpi_model:
        print(f"  🧮 CPI Model: {len(cpi_model)} thresholds evaluated")
    if catalysts:
        print(f"  ⚡ CATALYSTS: {len(catalysts)} events within 48h — HIGH OPPORTUNITY WINDOW")
    missing = []
    if not ODDS_API_KEY:
        missing.append("ODDS_API_KEY → https://the-odds-api.com (free 500/mo)")
    if not FRED_API_KEY:
        missing.append("FRED_API_KEY → https://fred.stlouisfed.org (free)")
    if missing:
        print(f"  ⚙️  Optional keys for .env:")
        for m in missing:
            print(f"     • {m}")
    print("=" * 65)

    # Log
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kalshi": len(kalshi), "poly": len(poly), "pi": len(pi),
        "odds": len(odds), "catalysts": len(catalysts),
        "cpi_model": cpi_model,
        "opps": len(opps),
        "details": [{k: v for k, v in o.items()} for o in opps]
    }
    with open(LOG_DIR / "arbitrage_v2.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return opps


if __name__ == "__main__":
    run()
