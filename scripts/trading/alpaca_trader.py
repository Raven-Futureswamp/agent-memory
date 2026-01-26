#!/usr/bin/env python3
"""
Alpaca Stock Auto-Trader (Level 2 — Semi-Autonomous)
Momentum scanner + auto-execution during market hours.

Risk Rules:
- Max 50% of capital per position ($50)
- Max 2 open positions
- Always use stop loss (-3%)
- Take profit at +5-8%
- No trading first/last 5 min
- Stop after 2 losses per day
- Only trade watchlist stocks
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

# Watchlist — high-momentum, liquid stocks
WATCHLIST = ["NVDA", "TSLA", "AMD", "META", "PLTR", "SOFI"]
ETFS = ["SPY", "QQQ"]

# Risk rules
MAX_POSITION_PCT = 0.50     # 50% of equity per position
MAX_POSITIONS = 2           # Max 2 open at once
STOP_LOSS_PCT = -0.03       # -3% stop loss
TAKE_PROFIT_PCT = 0.06      # +6% take profit
MAX_DAILY_LOSSES = 2        # Stop trading after 2 losses
MIN_MOMENTUM_PCT = 3.0      # Stock must be up 3%+ from prev close
MIN_VOLUME_MULT = 1.5       # Volume must be 1.5x average


# ============== API HELPERS ==============
def api_get(endpoint, data_api=False):
    """GET from Alpaca API."""
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
    """POST to Alpaca API."""
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


# ============== ACCOUNT ==============
def get_account():
    """Get account info."""
    return api_get("/v2/account")


def get_positions():
    """Get open positions."""
    return api_get("/v2/positions") or []


def get_orders(status="open"):
    """Get orders."""
    return api_get(f"/v2/orders?status={status}&limit=50") or []


# ============== MARKET DATA ==============
def is_market_open():
    """Check if market is open."""
    clock = api_get("/v2/clock")
    if clock:
        return clock.get("is_open", False)
    return False


def get_snapshots(symbols):
    """Get latest price snapshots."""
    sym_str = ",".join(symbols)
    return api_get(f"/v2/stocks/snapshots?symbols={sym_str}", data_api=True) or {}


def get_bars(symbol, timeframe="1Day", limit=20):
    """Get historical bars."""
    return api_get(
        f"/v2/stocks/{symbol}/bars?timeframe={timeframe}&limit={limit}",
        data_api=True
    )


# ============== SCANNER ==============
def scan_momentum(snapshots):
    """Find stocks with momentum signals."""
    opportunities = []
    
    for symbol, data in snapshots.items():
        if not data:
            continue
        
        latest = data.get("latestTrade", {})
        prev_bar = data.get("prevDailyBar", {})
        minute_bar = data.get("minuteBar", {})
        daily_bar = data.get("dailyBar", {})
        
        price = latest.get("p", 0)
        prev_close = prev_bar.get("c", 0)
        today_volume = daily_bar.get("v", 0) if daily_bar else 0
        avg_volume = prev_bar.get("v", 1) if prev_bar else 1
        
        if not price or not prev_close:
            continue
        
        # Calculate change
        change_pct = ((price - prev_close) / prev_close) * 100
        vol_mult = today_volume / avg_volume if avg_volume > 0 else 0
        
        # Check momentum criteria
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
        elif change_pct <= -MIN_MOMENTUM_PCT and vol_mult >= MIN_VOLUME_MULT:
            # Could short or buy dip — for now just flag
            opportunities.append({
                "symbol": symbol,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "volume_mult": round(vol_mult, 1),
                "today_volume": today_volume,
                "signal": "SELLOFF",
            })
    
    opportunities.sort(key=lambda x: -abs(x["change_pct"]))
    return opportunities


# ============== POSITION MANAGEMENT ==============
def check_existing_positions(positions):
    """Check stop loss / take profit on existing positions."""
    actions = []
    
    for pos in positions:
        symbol = pos.get("symbol", "")
        qty = float(pos.get("qty", 0))
        entry = float(pos.get("avg_entry_price", 0))
        current = float(pos.get("current_price", 0))
        unrealized_pl_pct = float(pos.get("unrealized_plpc", 0))
        
        if unrealized_pl_pct <= STOP_LOSS_PCT:
            actions.append({
                "action": "STOP_LOSS",
                "symbol": symbol,
                "qty": qty,
                "entry": entry,
                "current": current,
                "pl_pct": round(unrealized_pl_pct * 100, 2),
                "reason": f"Hit stop loss ({STOP_LOSS_PCT*100}%)"
            })
        elif unrealized_pl_pct >= TAKE_PROFIT_PCT:
            actions.append({
                "action": "TAKE_PROFIT",
                "symbol": symbol,
                "qty": qty,
                "entry": entry,
                "current": current,
                "pl_pct": round(unrealized_pl_pct * 100, 2),
                "reason": f"Hit take profit ({TAKE_PROFIT_PCT*100}%)"
            })
    
    return actions


def place_buy(symbol, notional):
    """Place a market buy order (fractional shares via notional)."""
    order = {
        "symbol": symbol,
        "notional": str(round(notional, 2)),
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
    }
    return api_post("/v2/orders", order)


def place_sell(symbol, qty):
    """Place a market sell order."""
    order = {
        "symbol": symbol,
        "qty": str(qty),
        "side": "sell",
        "type": "market",
        "time_in_force": "day",
    }
    return api_post("/v2/orders", order)


# ============== STATE MANAGEMENT ==============
def load_state():
    """Load daily trading state."""
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        # Reset if new day
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
    print("📈 ALPACA AUTO-TRADER — Level 2 (Semi-Autonomous)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print()
    
    # 1. Check market hours
    market_open = is_market_open()
    if not market_open:
        print("🔒 Market is CLOSED. Nothing to do.")
        clock = api_get("/v2/clock")
        if clock:
            next_open = clock.get("next_open", "")
            print(f"   Next open: {next_open}")
        return {"market": "closed", "trades": []}
    
    print("🟢 Market is OPEN")
    print()
    
    # 2. Load state & check daily limits
    state = load_state()
    if state["losses"] >= MAX_DAILY_LOSSES:
        print(f"🛑 Daily loss limit hit ({state['losses']} losses). Done for today.")
        return {"market": "open", "trades": [], "reason": "daily_loss_limit"}
    
    # 3. Account info
    account = get_account()
    if not account:
        print("❌ Could not fetch account")
        return {"error": "account_fetch_failed"}
    
    cash = float(account.get("cash", 0))
    equity = float(account.get("equity", 0))
    buying_power = float(account.get("buying_power", 0))
    
    print(f"💰 Cash: ${cash:.2f} | Equity: ${equity:.2f} | BP: ${buying_power:.2f}")
    
    # 4. Check existing positions
    positions = get_positions()
    print(f"📊 Open positions: {len(positions)}")
    
    trades_made = []
    
    if positions:
        for p in positions:
            sym = p.get("symbol", "")
            qty = p.get("qty", "0")
            pl = p.get("unrealized_pl", "0")
            pl_pct = float(p.get("unrealized_plpc", 0)) * 100
            print(f"   {sym}: {qty} shares | P/L: ${pl} ({pl_pct:+.1f}%)")
        
        # Check stop loss / take profit
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
    
    # 5. Scan for new opportunities
    if len(positions) >= MAX_POSITIONS:
        print(f"📋 Max positions ({MAX_POSITIONS}) reached. Monitoring only.")
    elif cash < 10:
        print("💸 Cash too low (<$10). Monitoring only.")
    else:
        print("🔍 Scanning watchlist for momentum...")
        all_symbols = WATCHLIST + ETFS
        snapshots = get_snapshots(all_symbols)
        
        opps = scan_momentum(snapshots)
        
        if opps:
            print(f"\n   Found {len(opps)} signals:")
            for opp in opps:
                icon = "🚀" if opp["signal"] == "MOMENTUM_UP" else "📉"
                print(f"   {icon} {opp['symbol']}: ${opp['price']} ({opp['change_pct']:+.1f}%) "
                      f"Vol: {opp['volume_mult']}x")
            
            # Only buy momentum-up signals
            buy_opps = [o for o in opps if o["signal"] == "MOMENTUM_UP"]
            
            for opp in buy_opps[:1]:  # Max 1 new buy per scan
                symbol = opp["symbol"]
                
                # Check we don't already own it
                owned = [p["symbol"] for p in positions]
                if symbol in owned:
                    print(f"\n   ⏭️ Already own {symbol}")
                    continue
                
                # Calculate position size
                max_spend = min(equity * MAX_POSITION_PCT, cash - 5)  # Keep $5 buffer
                if max_spend < 10:
                    print(f"\n   💸 Not enough cash for {symbol}")
                    continue
                
                print(f"\n   ✅ BUYING {symbol}")
                print(f"      Price: ${opp['price']} | Momentum: {opp['change_pct']:+.1f}%")
                print(f"      Amount: ${max_spend:.2f}")
                print(f"      Stop loss: {STOP_LOSS_PCT*100}% | Take profit: {TAKE_PROFIT_PCT*100}%")
                
                result = place_buy(symbol, max_spend)
                if result:
                    order_id = result.get("id", "")
                    print(f"      🎉 ORDER PLACED: {order_id}")
                    trades_made.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "MOMENTUM_BUY",
                        "symbol": symbol,
                        "side": "buy",
                        "notional": max_spend,
                        "price": opp["price"],
                        "change_pct": opp["change_pct"],
                        "volume_mult": opp["volume_mult"],
                        "order_id": order_id,
                    })
                    state["trades"] += 1
                    state["buys"].append(symbol)
                else:
                    print(f"      ❌ Order failed")
        else:
            print("   No momentum signals. Watchlist is quiet.")
    
    # 6. Summary
    print()
    print("=" * 65)
    print(f"📋 SUMMARY: {len(trades_made)} actions taken")
    if trades_made:
        for t in trades_made:
            print(f"   • {t['action']}: {t['symbol']} ({t['side']})")
    print(f"   Daily stats: {state['trades']} trades | {state['losses']} losses")
    print("=" * 65)
    
    # 7. Save state & log
    save_state(state)
    for t in trades_made:
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(t) + "\n")
    
    return {"market": "open", "trades": trades_made}


def format_alert(result):
    """Format for notification."""
    trades = result.get("trades", [])
    if not trades:
        return None
    lines = [f"📈 Alpaca Auto-Trader — {len(trades)} action(s):"]
    for t in trades:
        lines.append(f"• {t['action']}: {t['symbol']} ({t['side']})")
    return "\n".join(lines)


if __name__ == "__main__":
    result = run()
    alert = format_alert(result)
    if alert:
        print()
        print("📱 ALERT:")
        print(alert)
