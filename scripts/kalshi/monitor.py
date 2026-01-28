#!/usr/bin/env python3
"""
Kalshi Portfolio & Arbitrage Monitor
Runs every hour to check positions and find new opportunities.
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from kalshi_python import KalshiClient, Configuration

LOG_DIR = PROJECT_ROOT / "logs" / "kalshi"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_client():
    with open(PROJECT_ROOT / ".kalshi-private-key.pem", "r") as f:
        private_key = f.read()
    config = Configuration()
    config.api_key_id = "898f7406-b498-4205-8949-c9f137403966"
    config.private_key_pem = private_key
    return KalshiClient(configuration=config)

def get_polymarket_prices():
    """Get Polymarket prices for arbitrage comparison."""
    try:
        url = "https://gamma-api.polymarket.com/markets"
        response = requests.get(url, params={"closed": "false", "limit": 100}, timeout=30)
        data = response.json()
        
        prices = {}
        for m in data:
            question = m.get('question', '').lower()
            prices_raw = m.get('outcomePrices', '[]')
            if isinstance(prices_raw, str):
                prices_list = json.loads(prices_raw)
            else:
                prices_list = prices_raw
            
            if len(prices_list) >= 2:
                prices[question] = float(prices_list[0]) * 100
        return prices
    except:
        return {}

def check_portfolio(client):
    """Check current positions and P&L."""
    print("\n" + "="*70)
    print(f"📊 PORTFOLIO CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    balance = client._portfolio_api.get_balance()
    fills = client._portfolio_api.get_fills(limit=50)
    fill_list = fills.fills if hasattr(fills, 'fills') else []
    
    positions = {}
    for f in fill_list:
        ticker = f.ticker
        if ticker not in positions:
            positions[ticker] = {'count': 0, 'cost': 0, 'side': f.side}
        positions[ticker]['count'] += f.count
        if f.side == 'no':
            positions[ticker]['cost'] += f.count * (1 - f.price)
        else:
            positions[ticker]['cost'] += f.count * f.price
    
    total_cost = 0
    total_value = 0
    
    for ticker, pos in positions.items():
        try:
            market = client._markets_api.get_market(ticker=ticker)
            m = market.market if hasattr(market, 'market') else market
            title = m.title[:50] if hasattr(m, 'title') else ticker
            yes_bid = m.yes_bid / 100 if hasattr(m, 'yes_bid') else 0.5
        except:
            title = ticker
            yes_bid = 0.5
        
        # Current market value
        if pos['side'] == 'no':
            current_price = 1 - yes_bid
        else:
            current_price = yes_bid
        
        market_value = pos['count'] * current_price
        pnl = market_value - pos['cost']
        pnl_pct = (pnl / pos['cost']) * 100 if pos['cost'] > 0 else 0
        
        total_cost += pos['cost']
        total_value += market_value
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        print(f"\n{emoji} {title}")
        print(f"   {pos['count']} {pos['side'].upper()} | Cost: ${pos['cost']:.2f} | Value: ${market_value:.2f} | P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
    
    total_pnl = total_value - total_cost
    print(f"\n{'='*70}")
    print(f"💰 Cash: ${balance.balance/100:.2f}")
    print(f"📈 Positions: ${total_value:.2f} (cost: ${total_cost:.2f})")
    print(f"📊 Unrealized P&L: ${total_pnl:+.2f}")
    print(f"💼 Total Account: ${balance.balance/100 + total_value:.2f}")
    
    return balance.balance/100, total_cost, total_value

def check_arbitrage():
    """Check for arbitrage opportunities."""
    print("\n" + "="*70)
    print("🔍 ARBITRAGE SCAN")
    print("="*70)
    
    poly_prices = get_polymarket_prices()
    if not poly_prices:
        print("Could not fetch Polymarket prices")
        return []
    
    # Get Kalshi markets
    url = "https://api.elections.kalshi.com/trade-api/v2/events"
    response = requests.get(url, params={"status": "open", "limit": 200, "with_nested_markets": "true"}, timeout=30)
    events = response.json().get('events', [])
    
    opportunities = []
    
    # Keywords to match
    comparisons = [
        ('doge', 'spending', '250'),
        ('doge', 'cut', '250'),
        ('doge', 'spending', '1000'),
        ('trump', 'fed', 'end'),
        ('trump', 'balance', 'budget'),
        ('recession', '2025'),
        ('elon', 'trillionaire'),
    ]
    
    for e in events:
        for m in e.get('markets', []):
            title = m.get('title', '').lower()
            yes_bid = m.get('yes_bid', 0)
            volume = m.get('volume', 0)
            
            if volume < 1000:
                continue
            
            # Check against Polymarket
            for poly_q, poly_yes in poly_prices.items():
                # Simple keyword matching
                if any(all(kw in title and kw in poly_q for kw in comp) for comp in comparisons):
                    spread = abs(yes_bid - poly_yes)
                    if spread > 5:
                        opportunities.append({
                            'kalshi': m.get('title', '')[:50],
                            'kalshi_yes': yes_bid,
                            'polymarket': poly_q[:50],
                            'poly_yes': poly_yes,
                            'spread': spread,
                            'volume': volume
                        })
    
    if opportunities:
        opportunities.sort(key=lambda x: -x['spread'])
        print(f"\n🚨 Found {len(opportunities)} arbitrage opportunities!")
        for opp in opportunities[:5]:
            print(f"\n  Kalshi: {opp['kalshi']} - YES {opp['kalshi_yes']:.0f}%")
            print(f"  Polymarket: {opp['polymarket']} - YES {opp['poly_yes']:.1f}%")
            print(f"  SPREAD: {opp['spread']:.1f} points")
    else:
        print("No significant arbitrage opportunities found")
    
    return opportunities

def check_new_opportunities(client):
    """Look for new high-confidence opportunities."""
    print("\n" + "="*70)
    print("🎯 NEW OPPORTUNITIES")
    print("="*70)
    
    url = "https://api.elections.kalshi.com/trade-api/v2/events"
    response = requests.get(url, params={"status": "open", "limit": 200, "with_nested_markets": "true"}, timeout=30)
    events = response.json().get('events', [])
    
    opportunities = []
    
    for e in events:
        for m in e.get('markets', []):
            yes_bid = m.get('yes_bid', 0) or 0
            yes_ask = m.get('yes_ask', 0) or 0
            volume = m.get('volume', 0) or 0
            ticker = m.get('ticker', '').lower()
            
            # Skip esports and low volume
            if 'esport' in ticker or 'multigame' in ticker or volume < 5000:
                continue
            
            # High confidence NO (YES <= 10%)
            if yes_ask <= 10 and yes_ask > 0:
                roi = (yes_ask / (100 - yes_bid)) * 100
                opportunities.append({
                    'type': 'NO',
                    'title': m.get('title', '')[:50],
                    'ticker': m.get('ticker'),
                    'yes_price': yes_ask,
                    'cost': 100 - yes_bid,
                    'profit': yes_bid,
                    'roi': roi,
                    'volume': volume
                })
            
            # High confidence YES (>= 90%)
            elif yes_bid >= 90:
                roi = ((100 - yes_ask) / yes_ask) * 100
                opportunities.append({
                    'type': 'YES',
                    'title': m.get('title', '')[:50],
                    'ticker': m.get('ticker'),
                    'yes_price': yes_ask,
                    'cost': yes_ask,
                    'profit': 100 - yes_ask,
                    'roi': roi,
                    'volume': volume
                })
    
    if opportunities:
        opportunities.sort(key=lambda x: -x['roi'])
        print(f"\nFound {len(opportunities)} high-confidence opportunities:")
        for opp in opportunities[:10]:
            print(f"\n  {opp['type']}: {opp['title']}")
            print(f"  ROI: {opp['roi']:.1f}% | Volume: {opp['volume']:,}")
    else:
        print("No new high-confidence opportunities")
    
    return opportunities

def run_monitor():
    """Run full monitoring cycle."""
    client = get_client()
    
    # Check portfolio
    cash, cost, value = check_portfolio(client)
    
    # Check arbitrage
    arb_opps = check_arbitrage()
    
    # Check new opportunities
    new_opps = check_new_opportunities(client)
    
    # Log results
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'cash': cash,
        'invested': cost,
        'value': value,
        'arb_opportunities': len(arb_opps),
        'new_opportunities': len(new_opps)
    }
    
    with open(LOG_DIR / "monitor.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"\n✅ Monitor complete - logged to {LOG_DIR / 'monitor.jsonl'}")

if __name__ == "__main__":
    run_monitor()
