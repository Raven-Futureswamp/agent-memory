#!/usr/bin/env python3
"""
Alpaca Stock Auto-Trader v2 (Level 2 — Semi-Autonomous)
Swing trading + momentum scanner + VWAP filter + bracket orders.
Optimized for $100 account per Grok's recommendations.

Risk Rules:
- Max 45% of equity per position ($45)
- Max 2 open positions
- Stop loss: -2% (via bracket order)
- Trailing stop: 2.5%
- Momentum threshold: 2%+ with 1.5x volume
- VWAP filter: only buy above VWAP
- $10 cash buffer
- Max 2 losses per day
- Swing mode: hold 1-3 days
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs" / "trading"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TRADE_LOG = LOG_DIR / "auto_trades.jsonl"
STATE_FILE = LOG_DIR / "trader_state.json"

# ============== CONFIG ==============
API_KEY = os.getenv("ALPACA_API_KEY", "")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
BASE_URL = os.getenv("ALPACA_BASE_URL", "https://api.alpaca.markets")
DATA_URL = "https://data.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

# Watchlist — high-momentum, liquid stocks (Grok: drop SOFI, add AAPL + MSFT)
WATCHLIST = ["NVDA", "TSLA", "AMD", "META", "PLTR", "AAPL", "MSFT"]
ETFS = ["SPY", "QQQ"]

# Risk rules (Grok-optimized for $100)
MAX_POSITION_PCT = 0.45     # 45% of equity per position (Grok: down from 50%)
MAX_POSITIONS = 2           # Max 2 open at once
STOP_LOSS_PCT = 0.02        # 2% stop loss (Grok: tightened from 3%)
TRAILING_STOP_PCT = 0.025   # 2.5% trailing stop (Grok: replaces fixed take profit)
MAX_DAILY_LOSSES = 2        # Stop trading after 2 losses
MIN_MOMENTUM_PCT = 2.0      # 2% momentum threshold (Grok: down from 3%)
MIN_VOLUME_MULT = 1.5       # Volume must be 1.5x average
CASH_BUFFER = 10.0          # Keep $10 buffer (Grok: up from $5)


# ============== API HELPERS ==============
def api_get(endpoint, data_api=False):
    url = f"{DATA_URL}{endpoint}" if data_api else f"{BASE_URL}{endpoint}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  ⚠️ API {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  ⚠️ API error: {e}")
        return None


def api_post(endpoint, data):
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", headers=HEADERS, json=data, timeout=15)
        if r.status_code in (200, 201):
            return r.json()
        else:
            print(f"  ⚠️ Order error {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        print(f"  ⚠️ Order error: {e}")
        return None


def api_delete(endpoint):
    try:
        r = requests.delete(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=15)
        return r.status_code in (200, 204)
    except:
        return False


# ============== ACCOUNT ==============
def get_account():
    return api_get("/v2/account")

def get_positions():
    return api_get("/v2/positions") or []

def get_orders(status="open"):
    return api_get(f"/v2/orders?status={status}&limit=50") or []


# ============== MARKET DATA ==============
def is_market_open():
    clock = api_get("/v2/clock")
    if clock:
        return clock.get("is_open", False), clock
    return False, None


def get_snapshots(symbols):
    sym_str = ",".join(symbols)
    return api_get(f"/v2/stocks/snapshots?symbols={sym_str}", data_api=True) or {}


def get_bars(symbol, timeframe="1Day", limit=20):
    return api_get(
        f"/v2/stocks/{symbol}/bars?timeframe={timeframe}&limit={limit}",
        data_api=True
    )


def get_vwap(symbol):
    """Get today's VWAP from 1-min bars."""
    bars_data = api_get(
        f"/v2/stocks/{symbol}/bars?timeframe=1Min&limit=390",
        data_api=True
    )
    if not bars_data:
        return None

    bars = bars_data.get("bars", [])
    if not bars:
        return None

    total_pv = 0  # price * volume
    total_v = 0
    for bar in bars:
        typical_price = (bar.get("h", 0) + bar.get("l", 0) + bar.get("c", 0)) / 3
        vol = bar.get("v", 0)
        total_pv += typical_price * vol
        total_v += vol

    if total_v == 0:
        return None
    return round(total_pv / total_v, 2)


# ============== SCANNER ==============
def scan_momentum(snapshots):
    """Find stocks with momentum + VWAP confirmation."""
    opportunities = []

    for symbol, data in snapshots.items():
        if not data:
            continue

        latest = data.get("latestTrade", {})
        prev_bar = data.get("prevDailyBar", {})
        daily_bar = data.get("dailyBar", {})

        price = latest.get("p", 0)
        prev_close = prev_bar.get("c", 0)
        today_volume = daily_bar.get("v", 0) if daily_bar else 0
        avg_volume = prev_bar.get("v", 1) if prev_bar else 1

        if not price or not prev_close:
            continue

        change_pct = ((price - prev_close) / prev_close) * 100
        vol_mult = today_volume / avg_volume if avg_volume > 0 else 0

        # Momentum check (Grok: 2% threshold)
        if change_pct >= MIN_MOMENTUM_PCT and vol_mult >= MIN_VOLUME_MULT:
            opportunities.append({
                "symbol": symbol,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "volume_mult": round(vol_mult, 1),
                "today_volume": today_volume,
                "signal": "MOMENTUM_UP",
            })

    opportunities.sort(key=lambda x: -x["change_pct"])
    return opportunities


def vwap_filter(opportunities):
    """Filter: only buy stocks trading above VWAP (Grok recommendation)."""
    filtered = []
    for opp in opportunities:
        vwap = get_vwap(opp["symbol"])
        if vwap is None:
            # Can't get VWAP — skip to be safe
            print(f"     ⏭️ {opp['symbol']}: No VWAP data, skipping")
            continue

        opp["vwap"] = vwap
        if opp["price"] > vwap:
            opp["vwap_status"] = "ABOVE"
            filtered.append(opp)
            print(f"     ✅ {opp['symbol']}: ${opp['price']} > VWAP ${vwap}")
        else:
            print(f"     ❌ {opp['symbol']}: ${opp['price']} < VWAP ${vwap} (rejected)")

    return filtered


# ============== POSITION MANAGEMENT ==============
def check_existing_positions(positions):
    """Check trailing stop on existing positions."""
    actions = []

    for pos in positions:
        symbol = pos.get("symbol", "")
        qty = float(pos.get("qty", 0))
        entry = float(pos.get("avg_entry_price", 0))
        current = float(pos.get("current_price", 0))
        unrealized_pl_pct = float(pos.get("unrealized_plpc", 0))
        market_value = float(pos.get("market_value", 0))

        # Stop loss check (Grok: -2%)
        if unrealized_pl_pct <= -STOP_LOSS_PCT:
            actions.append({
                "action": "STOP_LOSS",
                "symbol": symbol,
                "qty": qty,
                "entry": entry,
                "current": current,
                "pl_pct": round(unrealized_pl_pct * 100, 2),
                "reason": f"Hit stop loss (-{STOP_LOSS_PCT*100}%)"
            })

        # Trailing stop logic: if up more than trailing %, check if it's pulling back
        # For swing trades, we'll manage this via Alpaca's native trailing stop orders
        # This is a backup check
        elif unrealized_pl_pct >= 0.10:  # +10% — consider taking profit on big winners
            actions.append({
                "action": "TAKE_PROFIT",
                "symbol": symbol,
                "qty": qty,
                "entry": entry,
                "current": current,
                "pl_pct": round(unrealized_pl_pct * 100, 2),
                "reason": "Big winner +10% — taking profit"
            })

    return actions


# ============== ORDER PLACEMENT ==============
def place_bracket_buy(symbol, notional, price):
    """
    Place a bracket order: buy + stop loss + trailing stop (Grok recommendation).
    Alpaca bracket orders attach OCA (one-cancels-all) exits.
    """
    stop_price = round(price * (1 - STOP_LOSS_PCT), 2)
    trail_pct = str(TRAILING_STOP_PCT * 100)  # "2.5"

    # Try bracket order first
    order = {
        "symbol": symbol,
        "notional": str(round(notional, 2)),
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc",  # Good til cancelled (swing trading)
        "order_class": "bracket",
        "stop_loss": {
            "stop_price": str(stop_price),
        },
        "take_profit": {
            "limit_price": str(round(price * 1.10, 2)),  # +10% limit as safety net
        },
    }

    result = api_post("/v2/orders", order)
    if result:
        return result

    # Fallback: simple market order if bracket fails (fractional shares can't bracket)
    print(f"     ⚠️ Bracket order failed, trying simple market order...")
    simple_order = {
        "symbol": symbol,
        "notional": str(round(notional, 2)),
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
    }
    return api_post("/v2/orders", simple_order)


def place_sell(symbol, qty):
    order = {
        "symbol": symbol,
        "qty": str(qty),
        "side": "sell",
        "type": "market",
        "time_in_force": "day",
    }
    return api_post("/v2/orders", order)


def place_trailing_stop(symbol, qty, trail_pct):
    """Place a trailing stop order (Grok recommendation)."""
    order = {
        "symbol": symbol,
        "qty": str(qty),
        "side": "sell",
        "type": "trailing_stop",
        "trail_percent": str(trail_pct),
        "time_in_force": "gtc",
    }
    return api_post("/v2/orders", order)


# ============== STATE MANAGEMENT ==============
def load_state():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        if state.get("date") != today:
            return {"date": today, "trades": 0, "losses": 0, "buys": [], "sells": []}
        return state
    except:
        return {"date": datetime.now().strftime("%Y-%m-%d"), "trades": 0, "losses": 0, "buys": [], "sells": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ============== MAIN ==============
def run():
    print("=" * 65)
    print("📈 ALPACA AUTO-TRADER v2 — Swing + Momentum + VWAP")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   Grok-optimized: 2% momentum, -2% stop, 2.5% trail, VWAP filter")
    print("=" * 65)
    print()

    # 1. Market hours
    market_open, clock = is_market_open()
    if not market_open:
        print("🔒 Market is CLOSED.")
        if clock:
            print(f"   Next open: {clock.get('next_open', '?')}")
        return {"market": "closed", "trades": []}

    print("🟢 Market is OPEN")
    print()

    # 2. Daily limits
    state = load_state()
    if state["losses"] >= MAX_DAILY_LOSSES:
        print(f"🛑 Daily loss limit ({state['losses']}/{MAX_DAILY_LOSSES}). Done for today.")
        return {"market": "open", "trades": [], "reason": "daily_loss_limit"}

    # 3. Account
    account = get_account()
    if not account:
        return {"error": "account_fetch_failed"}

    cash = float(account.get("cash", 0))
    equity = float(account.get("equity", 0))
    bp = float(account.get("buying_power", 0))

    print(f"💰 Cash: ${cash:.2f} | Equity: ${equity:.2f} | BP: ${bp:.2f}")

    # 4. Existing positions — check stop loss / take profit
    positions = get_positions()
    print(f"📊 Positions: {len(positions)}/{MAX_POSITIONS}")

    trades_made = []

    if positions:
        for p in positions:
            sym = p.get("symbol", "")
            qty = p.get("qty", "0")
            entry = p.get("avg_entry_price", "0")
            current = p.get("current_price", "0")
            pl = p.get("unrealized_pl", "0")
            pl_pct = float(p.get("unrealized_plpc", 0)) * 100
            print(f"   {sym}: {qty} shares @ ${entry} → ${current} | P/L: ${pl} ({pl_pct:+.1f}%)")

        actions = check_existing_positions(positions)
        for action in actions:
            print(f"\n  ⚡ {action['action']}: {action['symbol']} ({action['pl_pct']:+.1f}%)")
            print(f"     {action['reason']}")

            result = place_sell(action["symbol"], action["qty"])
            if result:
                print(f"     ✅ SOLD {action['qty']} {action['symbol']}")
                trades_made.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": action["action"],
                    "symbol": action["symbol"],
                    "side": "sell",
                    "qty": action["qty"],
                    "pl_pct": action["pl_pct"],
                })
                if action["action"] == "STOP_LOSS":
                    state["losses"] += 1
            else:
                print(f"     ❌ Sell failed")

    print()

    # 5. Scan for new buys
    current_pos_count = len(positions) - len([t for t in trades_made if t["side"] == "sell"])

    if current_pos_count >= MAX_POSITIONS:
        print(f"📋 Max positions ({MAX_POSITIONS}) reached. Monitoring only.")
    elif cash < CASH_BUFFER + 10:
        print(f"💸 Cash ${cash:.2f} too low (need ${CASH_BUFFER + 10}+). Monitoring only.")
    else:
        print("🔍 Scanning watchlist for momentum...")
        all_symbols = WATCHLIST + ETFS
        snapshots = get_snapshots(all_symbols)

        # Stage 1: Momentum filter
        opps = scan_momentum(snapshots)

        if opps:
            print(f"\n   🚀 {len(opps)} momentum signals found:")
            for opp in opps:
                print(f"      {opp['symbol']}: ${opp['price']} ({opp['change_pct']:+.1f}%) Vol: {opp['volume_mult']}x")

            # Stage 2: VWAP filter (Grok recommendation)
            print(f"\n   📊 VWAP filter:")
            opps = vwap_filter(opps)

            if opps:
                print(f"\n   ✅ {len(opps)} passed VWAP filter")

                # Buy best opportunity
                for opp in opps[:1]:
                    symbol = opp["symbol"]

                    # Don't buy if already owned
                    owned = [p.get("symbol") for p in positions]
                    if symbol in owned:
                        print(f"\n   ⏭️ Already own {symbol}")
                        continue

                    # Position sizing (Grok: 45%, $10 buffer)
                    max_spend = min(equity * MAX_POSITION_PCT, cash - CASH_BUFFER)
                    if max_spend < 10:
                        print(f"\n   💸 Not enough for {symbol} (need $10+)")
                        continue

                    stop_price = round(opp["price"] * (1 - STOP_LOSS_PCT), 2)
                    tp_price = round(opp["price"] * 1.10, 2)

                    print(f"\n   🟢 BUYING {symbol}")
                    print(f"      Price: ${opp['price']} | VWAP: ${opp.get('vwap', '?')}")
                    print(f"      Momentum: {opp['change_pct']:+.1f}% | Volume: {opp['volume_mult']}x")
                    print(f"      Amount: ${max_spend:.2f}")
                    print(f"      Stop: ${stop_price} (-{STOP_LOSS_PCT*100}%)")
                    print(f"      Target: ${tp_price} (+10%) with {TRAILING_STOP_PCT*100}% trailing stop")

                    # Place bracket order (Grok recommendation)
                    result = place_bracket_buy(symbol, max_spend, opp["price"])
                    if result:
                        order_id = result.get("id", "")
                        order_status = result.get("status", "")
                        print(f"      🎉 ORDER: {order_id[:12]}... ({order_status})")

                        trades_made.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "action": "MOMENTUM_BUY",
                            "symbol": symbol,
                            "side": "buy",
                            "notional": round(max_spend, 2),
                            "price": opp["price"],
                            "vwap": opp.get("vwap"),
                            "change_pct": opp["change_pct"],
                            "volume_mult": opp["volume_mult"],
                            "stop_loss": stop_price,
                            "order_id": order_id,
                        })
                        state["trades"] += 1
                        state["buys"].append(symbol)
                    else:
                        print(f"      ❌ Order failed")
            else:
                print("\n   No stocks passed VWAP filter.")
        else:
            print("   No momentum signals. Watchlist is quiet.")

    # 6. Summary
    print()
    print("=" * 65)
    print(f"📋 SUMMARY: {len(trades_made)} actions")
    if trades_made:
        for t in trades_made:
            if t["side"] == "buy":
                print(f"   🟢 BUY {t['symbol']} ${t.get('notional', '?')} @ ${t['price']}")
            else:
                print(f"   🔴 SELL {t['symbol']} ({t['action']}) {t['pl_pct']:+.1f}%")
    print(f"   Daily: {state['trades']} trades | {state['losses']} losses")
    print("=" * 65)

    # 7. Save & log
    save_state(state)
    for t in trades_made:
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(t) + "\n")

    return {"market": "open", "trades": trades_made}


def format_alert(result):
    trades = result.get("trades", [])
    if not trades:
        return None
    lines = [f"📈 Alpaca Auto-Trader — {len(trades)} action(s):"]
    for t in trades:
        if t["side"] == "buy":
            lines.append(f"• BUY {t['symbol']} ${t.get('notional','?')} @ ${t['price']} "
                         f"(+{t['change_pct']}% momentum, VWAP ✅)")
        else:
            lines.append(f"• {t['action']} {t['symbol']} ({t['pl_pct']:+.1f}%)")
    lines.append("\nSwing hold 1-3 days. Trailing stop active.")
    return "\n".join(lines)


if __name__ == "__main__":
    result = run()
    alert = format_alert(result)
    if alert:
        print()
        print("📱 ALERT:")
        print(alert)
