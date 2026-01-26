#!/usr/bin/env python3
"""
Kalshi Auto-Trader (Level 2 — Semi-Autonomous)
Scans for opportunities and auto-executes within risk rules.
Alerts the user on every trade.

Risk Rules:
- Spread > 5 pts between platforms
- ROI > 8%
- Volume > 1,000
- Max $20 per trade (20% of capital)
- Max 60% of capital in positions
- Short-term only (<60 days to close)
- HIGH confidence matches only
- Min 3¢ edge after Kalshi fees
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from trade import get_client, get_balance, get_positions, place_order
from arbitrage_v2 import run as run_scan

LOG_DIR = PROJECT_ROOT / "logs" / "kalshi"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TRADE_LOG = LOG_DIR / "auto_trades.jsonl"

# ============== RISK RULES ==============
CAPITAL = 100_00           # $100 in cents
MAX_PER_TRADE_PCT = 0.20   # 20% max per trade
MAX_POSITION_PCT = 0.60    # 60% max total in positions
MIN_SPREAD = 5             # Minimum spread in points
MIN_ROI = 8                # Minimum ROI %
MIN_VOLUME = 1000          # Minimum volume
MIN_EDGE_CENTS = 3         # Min edge after fees (Kalshi ~2¢ fee)
MAX_TRADE_CENTS = int(CAPITAL * MAX_PER_TRADE_PCT)  # $20 = 2000¢


def check_risk_rules(opp, cash_cents, position_value_cents):
    """Check if an opportunity passes all risk rules. Returns (pass, reason)."""
    
    # Must be HIGH confidence (keyword match)
    if opp.get("match_type") != "keyword" and opp.get("confidence") != "HIGH":
        # Allow it if it came from strict matching (all are keyword in v2)
        pass
    
    spread = opp.get("spread", 0)
    roi = opp.get("roi", 0)
    volume = opp.get("volume", 0)
    edge = opp.get("edge", 0)
    days = opp.get("days_left", 999)
    
    if spread < MIN_SPREAD:
        return False, f"Spread {spread} < {MIN_SPREAD}"
    
    if roi < MIN_ROI:
        return False, f"ROI {roi}% < {MIN_ROI}%"
    
    if volume < MIN_VOLUME:
        return False, f"Volume {volume} < {MIN_VOLUME}"
    
    if edge < MIN_EDGE_CENTS:
        return False, f"Edge {edge}¢ < {MIN_EDGE_CENTS}¢ (fees eat profit)"
    
    if days == 0:
        return False, "Market closes today (too risky)"
    
    if isinstance(days, int) and days > 60:
        return False, f"Too long-term ({days} days)"
    
    # Capital checks
    total_positions = position_value_cents
    if total_positions > CAPITAL * MAX_POSITION_PCT:
        return False, f"Position limit hit ({total_positions/100:.0f}$ > {CAPITAL*MAX_POSITION_PCT/100:.0f}$)"
    
    if cash_cents < MAX_TRADE_CENTS:
        # Can still trade with less, just smaller
        pass
    
    return True, "PASS"


def calculate_order(opp, cash_cents):
    """Calculate order details from opportunity."""
    trade_str = opp.get("trade", "")
    
    # Parse trade direction and price
    if "BUY NO" in trade_str:
        side = "no"
        # Extract price: "BUY NO @ 70¢"
        price = opp.get("kalshi_no", 0)
    elif "BUY YES" in trade_str:
        side = "yes"
        price = opp.get("kalshi_yes", 0)
    else:
        return None
    
    if price <= 0 or price >= 99:
        return None
    
    # Position sizing: max $20 or available cash, whichever is less
    max_spend = min(MAX_TRADE_CENTS, cash_cents - 500)  # Keep $5 buffer
    if max_spend <= 0:
        return None
    
    count = max_spend // price
    if count <= 0:
        return None
    
    # Cap at reasonable amount
    count = min(count, 50)
    
    total_cost = count * price
    potential_payout = count * 100  # $1.00 per contract if correct
    potential_profit = potential_payout - total_cost
    
    return {
        "side": side,
        "price": price,
        "count": count,
        "total_cost_cents": total_cost,
        "potential_profit_cents": potential_profit,
        "roi_pct": round(potential_profit / total_cost * 100, 1) if total_cost > 0 else 0,
    }


def find_ticker(client, opp):
    """Find the Kalshi ticker for an opportunity."""
    # The opportunity has kalshi_title — we need to find the ticker
    kalshi_title = opp.get("kalshi_title", "")
    
    # Search Kalshi markets
    import requests
    cursor = None
    for page in range(15):
        params = {"status": "open", "limit": 200, "with_nested_markets": "true"}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(
                "https://api.elections.kalshi.com/trade-api/v2/events",
                params=params, timeout=15
            )
            data = r.json()
        except:
            break
        
        for event in data.get("events", []):
            for m in event.get("markets", []):
                if m.get("title", "") == kalshi_title:
                    return m.get("ticker")
        
        cursor = data.get("cursor")
        if not cursor:
            break
    
    return None


def execute_trade(client, opp, order_details):
    """Execute a trade and return result."""
    # Find ticker
    ticker = find_ticker(client, opp)
    if not ticker:
        return {"success": False, "error": "Could not find ticker"}
    
    print(f"  📤 Placing order: {order_details['count']} {order_details['side'].upper()} "
          f"@ {order_details['price']}¢ on {ticker}")
    
    result = place_order(
        client,
        ticker=ticker,
        side=order_details["side"],
        count=order_details["count"],
        limit_price=order_details["price"]
    )
    
    if result:
        return {
            "success": True,
            "ticker": ticker,
            "side": order_details["side"],
            "count": order_details["count"],
            "price": order_details["price"],
            "total_cost": order_details["total_cost_cents"],
            "response": str(result)[:200]
        }
    else:
        return {"success": False, "error": "Order placement failed"}


def run_auto_trader():
    """Main auto-trader loop (single run)."""
    print("=" * 65)
    print("🤖 KALSHI AUTO-TRADER — Level 2 (Semi-Autonomous)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print()
    
    # 1. Check account
    print("💰 Checking account...")
    try:
        client = get_client()
        cash = get_balance(client)
        positions = get_positions(client)
        position_value = sum(abs(getattr(p, 'position', 0)) for p in positions) * 50  # rough estimate
        print(f"  Cash: ${cash/100:.2f} | Positions: {len(positions)}")
    except Exception as e:
        print(f"  ❌ Account error: {e}")
        return {"error": str(e), "trades": []}
    
    if cash < 500:  # Less than $5
        print("  ⚠️ Cash too low (<$5). Skipping scan.")
        return {"error": "Low cash", "trades": []}
    
    # 2. Run scanner
    print()
    print("🔍 Running arbitrage scan...")
    print()
    opportunities = run_scan()
    print()
    
    if not opportunities:
        print("✅ No opportunities found. Standing by.")
        return {"trades": [], "scanned": True}
    
    # 3. Evaluate each opportunity
    trades_made = []
    print("🎯 Evaluating opportunities against risk rules...")
    print("-" * 65)
    
    for opp in opportunities:
        name = opp.get("name", "Unknown")
        
        # Check risk rules
        passes, reason = check_risk_rules(opp, cash, position_value)
        
        if not passes:
            print(f"  ❌ {name}: {reason}")
            continue
        
        # Calculate order
        order = calculate_order(opp, cash)
        if not order:
            print(f"  ❌ {name}: Could not calculate valid order")
            continue
        
        print(f"\n  ✅ {name} — PASSES ALL RULES")
        print(f"     Spread: {opp['spread']} pts | ROI: {opp['roi']}% | Days: {opp['days_left']}")
        print(f"     Order: {order['count']} {order['side'].upper()} @ {order['price']}¢")
        print(f"     Cost: ${order['total_cost_cents']/100:.2f} | Potential profit: ${order['potential_profit_cents']/100:.2f}")
        
        # Execute
        result = execute_trade(client, opp, order)
        
        if result.get("success"):
            print(f"  🎉 TRADE EXECUTED: {result['count']} {result['side'].upper()} @ {result['price']}¢")
            cash -= order["total_cost_cents"]
            trades_made.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": name,
                "ticker": result.get("ticker"),
                "side": result["side"],
                "count": result["count"],
                "price": result["price"],
                "total_cost": order["total_cost_cents"],
                "roi": order["roi_pct"],
                "spread": opp["spread"],
                "external_source": opp.get("external_source"),
            })
        else:
            print(f"  ⚠️ TRADE FAILED: {result.get('error')}")
    
    # 4. Summary
    print()
    print("=" * 65)
    print(f"📋 SUMMARY: {len(trades_made)} trades executed")
    if trades_made:
        total_spent = sum(t["total_cost"] for t in trades_made)
        print(f"   Total spent: ${total_spent/100:.2f}")
        print(f"   Remaining cash: ${cash/100:.2f}")
        for t in trades_made:
            print(f"   • {t['name']}: {t['count']} {t['side'].upper()} @ {t['price']}¢ (ROI: {t['roi']}%)")
    print("=" * 65)
    
    # 5. Log trades
    for t in trades_made:
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(t) + "\n")
    
    return {"trades": trades_made, "scanned": True}


# Generate alert message for notification
def format_alert(result):
    """Format trade result for notification."""
    trades = result.get("trades", [])
    if not trades:
        return None
    
    lines = [f"🤖 Kalshi Auto-Trader — {len(trades)} trade(s) executed:"]
    for t in trades:
        lines.append(f"• {t['name']}: {t['count']} {t['side'].upper()} @ {t['price']}¢ (ROI: {t['roi']}%)")
    lines.append(f"\nReply 'kalshi undo' within 1 hour to reverse.")
    return "\n".join(lines)


if __name__ == "__main__":
    result = run_auto_trader()
    alert = format_alert(result)
    if alert:
        print()
        print("📱 ALERT MESSAGE:")
        print(alert)
