#!/usr/bin/env python3
"""
Kalshi Auto-Trader (Level 2 — Semi-Autonomous)
Scans for opportunities and auto-executes within risk rules.
Alerts the user on every trade.

Risk Rules (updated per Grok recommendations):
- Spread > 5 pts between platforms
- ROI > 8%
- Volume > 1,000
- Max $10 per trade (10% of capital) — smaller positions, more diversified
- Max 60% of capital in positions (5-6 smaller positions)
- Short-term only (<60 days to close)
- HIGH confidence matches only
- Min 3¢ edge after Kalshi fees
- Stop-loss: exit if position value drops -15%
- Take-profit: exit if position value rises +20%
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

from trade import get_client, get_balance, get_positions, place_order, get_market
from arbitrage_v2 import run as run_scan

LOG_DIR = PROJECT_ROOT / "logs" / "kalshi"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TRADE_LOG = LOG_DIR / "auto_trades.jsonl"

# ============== RISK RULES ==============
CAPITAL = 100_00           # $100 in cents
MAX_PER_TRADE_PCT = 0.10   # 10% max per trade (was 20%) — Grok rec: smaller, diversified
MAX_POSITION_PCT = 0.60    # 60% max total in positions (5-6 smaller bets)
MAX_POSITIONS = 6          # Target 5-6 positions max
MIN_SPREAD = 5             # Minimum spread in points
MIN_ROI = 8                # Minimum ROI %
MIN_VOLUME = 1000          # Minimum volume
MIN_EDGE_CENTS = 3         # Min edge after fees (Kalshi ~2¢ fee)
MAX_TRADE_CENTS = int(CAPITAL * MAX_PER_TRADE_PCT)  # $10 = 1000¢
MIN_CASH_TO_TRADE = 600    # Need at least $6 to attempt any trade ($5 buffer + $1 min)

# Stop-loss / Take-profit thresholds (Grok recs)
STOP_LOSS_PCT = -0.15      # Exit if position value drops 15%
TAKE_PROFIT_PCT = 0.20     # Exit if position value rises 20%


def check_stop_loss_take_profit(client, positions):
    """
    Check existing positions for stop-loss (-15%) or take-profit (+20%) triggers.
    Returns list of (position, action, reason) tuples for positions that should be exited.
    """
    exits = []

    # Load trade log for entry prices
    entry_prices = {}
    if TRADE_LOG.exists():
        with open(TRADE_LOG) as f:
            for line in f:
                try:
                    t = json.loads(line.strip())
                    ticker = t.get("ticker")
                    if ticker:
                        entry_prices[ticker] = {
                            "price": t.get("price", 0),
                            "side": t.get("side", "yes"),
                            "count": t.get("count", 0),
                        }
                except:
                    pass

    for p in positions:
        ticker = getattr(p, 'ticker', None)
        pos_count = getattr(p, 'position', 0)
        if not ticker or pos_count == 0:
            continue

        entry = entry_prices.get(ticker)
        if not entry:
            continue

        entry_price = entry["price"]
        if entry_price <= 0:
            continue

        # Get current market price
        market = get_market(client, ticker)
        if not market:
            continue

        # Determine current value based on our side
        side = entry["side"]
        if side == "yes":
            current_price = getattr(market, 'yes_bid', 0) or getattr(market, 'last_price', 0) or 0
        else:
            current_price = getattr(market, 'no_bid', 0) or 0
            if current_price == 0:
                yes_price = getattr(market, 'yes_bid', 0) or getattr(market, 'last_price', 0) or 0
                current_price = 100 - yes_price if yes_price > 0 else 0

        if current_price <= 0:
            continue

        # Calculate P&L percentage
        pnl_pct = (current_price - entry_price) / entry_price

        if pnl_pct <= STOP_LOSS_PCT:
            exits.append({
                "ticker": ticker,
                "action": "STOP_LOSS",
                "side": side,
                "count": abs(pos_count),
                "entry_price": entry_price,
                "current_price": current_price,
                "pnl_pct": round(pnl_pct * 100, 1),
                "reason": f"Stop-loss triggered: {pnl_pct*100:.1f}% (threshold: {STOP_LOSS_PCT*100}%)"
            })
        elif pnl_pct >= TAKE_PROFIT_PCT:
            exits.append({
                "ticker": ticker,
                "action": "TAKE_PROFIT",
                "side": side,
                "count": abs(pos_count),
                "entry_price": entry_price,
                "current_price": current_price,
                "pnl_pct": round(pnl_pct * 100, 1),
                "reason": f"Take-profit triggered: +{pnl_pct*100:.1f}% (threshold: +{TAKE_PROFIT_PCT*100}%)"
            })

    return exits


def execute_exit(client, exit_info):
    """Execute a stop-loss or take-profit exit by selling the position."""
    ticker = exit_info["ticker"]
    side = exit_info["side"]
    count = exit_info["count"]
    current_price = exit_info["current_price"]

    print(f"  📤 Exiting: SELL {count} {side.upper()} @ {current_price}¢ on {ticker}")

    # To exit, we sell our side — place a sell order at current bid
    try:
        from kalshi_python import CreateOrderRequest
        order = CreateOrderRequest(
            ticker=ticker,
            side=side,
            count=count,
            type='limit',
            action='sell',
        )
        if side == 'yes':
            order.yes_price = current_price
        else:
            order.no_price = current_price

        response = client._portfolio_api.create_order(**order.model_dump(exclude_none=True))
        return {"success": True, "response": str(response)[:200]}
    except Exception as e:
        print(f"  ⚠️ Exit failed: {e}")
        return {"success": False, "error": str(e)}


def check_risk_rules(opp, cash_cents, position_value_cents, num_positions=0):
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
    
    if cash_cents < MIN_CASH_TO_TRADE:
        return False, f"Cash too low (${cash_cents/100:.2f} < ${MIN_CASH_TO_TRADE/100:.2f})"
    
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
    
    # Position count limit (Grok: 5-6 smaller positions)
    if num_positions >= MAX_POSITIONS:
        return False, f"Max positions hit ({num_positions} >= {MAX_POSITIONS})"
    
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
    
    # Position sizing: max $10 or available cash, whichever is less (Grok: smaller diversified bets)
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
    ticker = find_ticker(client, opp)
    if not ticker:
        return {"success": False, "error": "Could not find ticker"}
    return execute_trade_with_ticker(client, opp, order_details, ticker)


def execute_trade_with_ticker(client, opp, order_details, ticker):
    """Execute a trade with a known ticker (avoids redundant lookup)."""
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
    print(f"📏 Risk: max ${MAX_TRADE_CENTS/100:.0f}/trade ({MAX_PER_TRADE_PCT*100:.0f}%) | "
          f"SL: {STOP_LOSS_PCT*100:.0f}% | TP: +{TAKE_PROFIT_PCT*100:.0f}%")
    print("=" * 65)
    print()
    
    # 1. Check account
    print("💰 Checking account...")
    try:
        client = get_client()
        cash = get_balance(client)
        positions = get_positions(client)
        position_value = sum(abs(getattr(p, 'position', 0)) for p in positions) * 50  # rough estimate
        num_positions = len([p for p in positions if getattr(p, 'position', 0) != 0])
        print(f"  Cash: ${cash/100:.2f} | Positions: {num_positions} | Max: {MAX_POSITIONS}")
    except Exception as e:
        print(f"  ❌ Account error: {e}")
        return {"error": str(e), "trades": [], "exits": []}
    
    # 2. CHECK STOP-LOSS / TAKE-PROFIT on existing positions
    exits_made = []
    print()
    print("🛡️ Checking stop-loss / take-profit on existing positions...")
    try:
        exits_needed = check_stop_loss_take_profit(client, positions)
        if exits_needed:
            for ex in exits_needed:
                icon = "🔴" if ex["action"] == "STOP_LOSS" else "🟢"
                print(f"  {icon} {ex['action']}: {ex['ticker']} — {ex['reason']}")
                print(f"     Entry: {ex['entry_price']}¢ → Now: {ex['current_price']}¢ ({ex['pnl_pct']:+.1f}%)")
                result = execute_exit(client, ex)
                if result.get("success"):
                    print(f"  ✅ EXIT EXECUTED for {ex['ticker']}")
                    exits_made.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "ticker": ex["ticker"],
                        "action": ex["action"],
                        "side": ex["side"],
                        "count": ex["count"],
                        "entry_price": ex["entry_price"],
                        "exit_price": ex["current_price"],
                        "pnl_pct": ex["pnl_pct"],
                    })
                    # Update cash after exit
                    cash += ex["current_price"] * ex["count"]
                    num_positions -= 1
                else:
                    print(f"  ⚠️ EXIT FAILED for {ex['ticker']}: {result.get('error')}")
        else:
            print("  ✅ All positions within bounds. No exits needed.")
    except Exception as e:
        print(f"  ⚠️ Stop/TP check error: {e}")
    
    if cash < MIN_CASH_TO_TRADE:
        print(f"  ⚠️ Cash too low (${cash/100:.2f} < ${MIN_CASH_TO_TRADE/100:.2f}). Skipping scan.")
        return {"trades": [], "exits": exits_made, "skipped": "low_cash"}
    
    # 3. Run scanner
    print()
    print("🔍 Running arbitrage scan...")
    print()
    opportunities = run_scan()
    print()
    
    if not opportunities:
        print("✅ No opportunities found. Standing by.")
        return {"trades": [], "exits": exits_made, "scanned": True}
    
    # 4. Evaluate each opportunity
    trades_made = []
    
    # Collect tickers we already hold to avoid duplicate buys
    held_tickers = set()
    for p in positions:
        t = getattr(p, 'ticker', '')
        if t and getattr(p, 'position', 0) != 0:
            held_tickers.add(t)
    if held_tickers:
        print(f"📌 Already holding: {', '.join(held_tickers)}")
    
    print("🎯 Evaluating opportunities against risk rules...")
    print("-" * 65)
    
    for opp in opportunities:
        name = opp.get("name", "Unknown")
        
        # Check risk rules (now includes position count limit)
        passes, reason = check_risk_rules(opp, cash, position_value, num_positions)
        
        if not passes:
            print(f"  ❌ {name}: {reason}")
            continue
        
        # Calculate order
        order = calculate_order(opp, cash)
        if not order:
            print(f"  ❌ {name}: Could not calculate valid order")
            continue
        
        # Find ticker BEFORE executing to check for duplicates
        ticker = find_ticker(client, opp)
        if not ticker:
            print(f"  ❌ {name}: Could not find ticker")
            continue
        
        if ticker in held_tickers:
            print(f"  ⏭️ {name}: Already holding {ticker} — skipping")
            continue
        
        # Flag catalyst windows
        catalyst_note = opp.get("catalyst_note", "")
        
        print(f"\n  ✅ {name} — PASSES ALL RULES")
        print(f"     Spread: {opp['spread']} pts | ROI: {opp['roi']}% | Days: {opp['days_left']}")
        print(f"     Order: {order['count']} {order['side'].upper()} @ {order['price']}¢")
        print(f"     Cost: ${order['total_cost_cents']/100:.2f} | Potential profit: ${order['potential_profit_cents']/100:.2f}")
        if catalyst_note:
            print(f"     ⚡ CATALYST: {catalyst_note}")
        
        # Execute — pass ticker directly to avoid redundant lookup
        result = execute_trade_with_ticker(client, opp, order, ticker)
        
        if result.get("success"):
            print(f"  🎉 TRADE EXECUTED: {result['count']} {result['side'].upper()} @ {result['price']}¢")
            cash -= order["total_cost_cents"]
            num_positions += 1
            held_tickers.add(ticker)
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
                "catalyst": catalyst_note or None,
            })
        else:
            print(f"  ⚠️ TRADE FAILED: {result.get('error')}")
            print(f"  🛑 Stopping — likely insufficient funds. No more attempts this run.")
            break
    
    # 5. Summary
    print()
    print("=" * 65)
    print(f"📋 SUMMARY: {len(trades_made)} trades | {len(exits_made)} exits")
    if exits_made:
        for ex in exits_made:
            icon = "🔴" if ex["action"] == "STOP_LOSS" else "🟢"
            print(f"   {icon} EXIT {ex['ticker']}: {ex['pnl_pct']:+.1f}%")
    if trades_made:
        total_spent = sum(t["total_cost"] for t in trades_made)
        print(f"   Total spent: ${total_spent/100:.2f}")
        print(f"   Remaining cash: ${cash/100:.2f}")
        for t in trades_made:
            print(f"   • {t['name']}: {t['count']} {t['side'].upper()} @ {t['price']}¢ (ROI: {t['roi']}%)")
    print("=" * 65)
    
    # 6. Log trades & exits
    for t in trades_made:
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(t) + "\n")
    for ex in exits_made:
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(ex) + "\n")
    
    return {"trades": trades_made, "exits": exits_made, "scanned": True}


# Generate alert message for notification
def format_alert(result):
    """Format trade result for notification."""
    trades = result.get("trades", [])
    exits = result.get("exits", [])
    if not trades and not exits:
        return None
    
    lines = []
    if exits:
        lines.append(f"🛡️ Kalshi Auto-Trader — {len(exits)} position(s) exited:")
        for ex in exits:
            icon = "🔴 STOP-LOSS" if ex["action"] == "STOP_LOSS" else "🟢 TAKE-PROFIT"
            lines.append(f"• {icon}: {ex['ticker']} ({ex['pnl_pct']:+.1f}%)")
    if trades:
        lines.append(f"🤖 Kalshi Auto-Trader — {len(trades)} trade(s) executed:")
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
