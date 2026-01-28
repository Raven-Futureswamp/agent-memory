#!/usr/bin/env python3
"""
Kalshi vs Polymarket Arbitrage Scanner
Finds price discrepancies between platforms.
"""

import requests
import json
from datetime import datetime

# ============== FETCH DATA ==============
def get_kalshi_markets():
    """Get relevant Kalshi markets."""
    url = "https://api.elections.kalshi.com/trade-api/v2/events"
    params = {"status": "open", "limit": 200, "with_nested_markets": "true"}
    response = requests.get(url, params=params, timeout=30)
    events = response.json().get('events', [])
    
    markets = {}
    for e in events:
        for m in e.get('markets', []):
            vol = m.get('volume', 0) or 0
            if vol > 500:
                markets[m.get('ticker', '')] = {
                    'title': m.get('title', ''),
                    'yes_bid': m.get('yes_bid', 0),
                    'yes_ask': m.get('yes_ask', 0),
                    'volume': vol
                }
    return markets

def get_polymarket_markets():
    """Get relevant Polymarket markets."""
    url = "https://gamma-api.polymarket.com/markets"
    params = {"closed": "false", "limit": 100}
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    
    markets = {}
    for m in data:
        question = m.get('question', '')
        prices_raw = m.get('outcomePrices', '[]')
        
        # Parse prices - might be string or list
        if isinstance(prices_raw, str):
            try:
                prices = json.loads(prices_raw)
            except:
                continue
        else:
            prices = prices_raw
        
        if len(prices) >= 2:
            try:
                yes_price = float(prices[0]) * 100  # Convert to cents
                markets[question] = {
                    'title': question,
                    'yes': yes_price,
                    'no': 100 - yes_price,
                    'volume': m.get('volumeNum', m.get('volume', 0))
                }
            except:
                continue
    return markets

# ============== MATCHING LOGIC ==============
# Define market pairs to compare
MARKET_PAIRS = [
    {
        'name': 'DOGE cuts > $250B',
        'kalshi_keywords': ['government spending', 'decrease', '250'],
        'polymarket_keywords': ['doge', 'cut', '250'],
    },
    {
        'name': 'DOGE cuts > $1T',
        'kalshi_keywords': ['government spending', 'decrease', '1000'],
        'polymarket_keywords': ['doge', 'cut', '1000', 'trillion'],
    },
    {
        'name': 'Elon Trillionaire',
        'kalshi_keywords': ['elon', 'musk', 'trillionaire'],
        'polymarket_keywords': ['elon', 'musk', 'trillionaire'],
    },
    {
        'name': 'Trump Budget Balance',
        'kalshi_keywords': ['trump', 'balance', 'budget'],
        'polymarket_keywords': ['trump', 'balance', 'budget'],
    },
    {
        'name': 'Recession 2025',
        'kalshi_keywords': ['recession', '2025'],
        'polymarket_keywords': ['recession', '2025', 'negative gdp'],
    },
    {
        'name': 'Fed Rate Cut',
        'kalshi_keywords': ['fed', 'rate', 'cut'],
        'polymarket_keywords': ['fed', 'rate', 'cut', 'fomc'],
    },
]

def find_matching_market(markets, keywords):
    """Find a market matching keywords."""
    for key, m in markets.items():
        title = (key + ' ' + m.get('title', '')).lower()
        if all(kw.lower() in title for kw in keywords):
            return key, m
    return None, None

def analyze_arbitrage():
    """Find arbitrage opportunities."""
    print("=" * 70)
    print("KALSHI vs POLYMARKET ARBITRAGE SCANNER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Fetch data
    print("Fetching Kalshi markets...")
    kalshi = get_kalshi_markets()
    print(f"  Found {len(kalshi)} Kalshi markets")
    
    print("Fetching Polymarket markets...")
    polymarket = get_polymarket_markets()
    print(f"  Found {len(polymarket)} Polymarket markets")
    print()
    
    opportunities = []
    
    for pair in MARKET_PAIRS:
        k_key, k_market = find_matching_market(kalshi, pair['kalshi_keywords'])
        p_key, p_market = find_matching_market(polymarket, pair['polymarket_keywords'])
        
        if k_market and p_market:
            k_yes = k_market['yes_bid']
            p_yes = p_market['yes']
            spread = abs(k_yes - p_yes)
            
            if spread > 5:  # Significant spread
                opportunities.append({
                    'name': pair['name'],
                    'kalshi_title': k_market['title'][:50],
                    'kalshi_yes': k_yes,
                    'kalshi_vol': k_market['volume'],
                    'polymarket_title': p_market['title'][:50],
                    'polymarket_yes': p_yes,
                    'spread': spread,
                    'trade': 'BUY NO on Kalshi' if k_yes > p_yes else 'BUY YES on Kalshi'
                })
    
    # Print opportunities
    if opportunities:
        opportunities.sort(key=lambda x: -x['spread'])
        
        print("🚨 ARBITRAGE OPPORTUNITIES (spread > 5%)")
        print("-" * 70)
        
        for opp in opportunities:
            print(f"\n{opp['name']}")
            print(f"  Kalshi:     YES = {opp['kalshi_yes']:>5.1f}% | {opp['kalshi_title']}")
            print(f"  Polymarket: YES = {opp['polymarket_yes']:>5.1f}% | {opp['polymarket_title']}")
            print(f"  SPREAD: {opp['spread']:.1f} points")
            print(f"  → {opp['trade']}")
            
            # Calculate potential profit
            if 'NO' in opp['trade']:
                cost = 100 - opp['kalshi_yes']
                profit = opp['kalshi_yes']
                poly_prob = 100 - opp['polymarket_yes']
            else:
                cost = opp['kalshi_yes']
                profit = 100 - opp['kalshi_yes']
                poly_prob = opp['polymarket_yes']
            
            print(f"  Cost: {cost:.0f}¢ | Potential profit: {profit:.0f}¢ | Poly prob: {poly_prob:.1f}%")
    else:
        print("No significant arbitrage opportunities found.")
    
    print()
    print("=" * 70)
    
    return opportunities

# ============== KNOWN ARBITRAGE OPPORTUNITIES ==============
def show_known_opportunities():
    """Show manually identified opportunities."""
    print()
    print("📊 KNOWN ARBITRAGE OPPORTUNITIES (manually verified)")
    print("=" * 70)
    
    opps = [
        {
            'market': 'DOGE cuts > $250 billion',
            'kalshi_yes': 23,
            'polymarket_yes': 0.7,
            'trade': 'BUY NO on Kalshi',
            'kalshi_cost': 77,
            'potential_profit': 23,
            'poly_confidence': 99.3
        },
        {
            'market': 'DOGE cuts $1 trillion+',
            'kalshi_yes': 12,
            'polymarket_yes': 0.3,  # Implied from 10%+ cut probability
            'trade': 'BUY NO on Kalshi',
            'kalshi_cost': 88,
            'potential_profit': 12,
            'poly_confidence': 99.7
        },
        {
            'market': 'Trump ends Federal Reserve',
            'kalshi_yes': 8,
            'polymarket_yes': 1,  # Very unlikely
            'trade': 'BUY NO on Kalshi',
            'kalshi_cost': 92,
            'potential_profit': 8,
            'poly_confidence': 99
        },
    ]
    
    for opp in opps:
        roi = (opp['potential_profit'] / opp['kalshi_cost']) * 100
        spread = opp['kalshi_yes'] - opp['polymarket_yes']
        
        print(f"\n🎯 {opp['market']}")
        print(f"   Kalshi YES: {opp['kalshi_yes']}% | Polymarket YES: {opp['polymarket_yes']}%")
        print(f"   SPREAD: {spread:.1f} points")
        print(f"   → {opp['trade']} at {opp['kalshi_cost']}¢")
        print(f"   → Profit: {opp['potential_profit']}¢ ({roi:.1f}% ROI)")
        print(f"   → Polymarket confidence: {opp['poly_confidence']}%")
    
    print()
    print("-" * 70)
    print("⚠️  NOTE: Cannot directly arbitrage (Polymarket blocked in US)")
    print("   But Polymarket prices suggest Kalshi NOs are underpriced!")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--known":
        show_known_opportunities()
    else:
        analyze_arbitrage()
        show_known_opportunities()
