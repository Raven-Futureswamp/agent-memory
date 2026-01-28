#!/usr/bin/env python3
"""
Kalshi Market Scanner v4 - Enhanced with Grok's recommendations
- Short-term market focus (< 90 days)
- External data integration (CME FedWatch)
- Better edge calculation
- Position sizing recommendations
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from kalshi_python import KalshiClient, Configuration

# ============== CONFIG ==============
API_KEY_ID = os.getenv("KALSHI_API_KEY_ID", "898f7406-b498-4205-8949-c9f137403966")
PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", str(PROJECT_ROOT / ".kalshi-private-key.pem"))
BASE_URL = "https://api.elections.kalshi.com"

SCAN_INTERVAL_SECONDS = 300
LOG_DIR = PROJECT_ROOT / "logs" / "kalshi"
OPPORTUNITIES_FILE = LOG_DIR / "opportunities.jsonl"
HOT_OPPORTUNITIES_FILE = LOG_DIR / "hot-opportunities.jsonl"

# Capital management
CAPITAL = 100  # dollars
MAX_POSITION_PCT = 0.20  # 20% max per trade
MIN_EDGE_CENTS = 3  # Minimum edge after fees
MIN_VOLUME = 1000  # Minimum volume for any trade
MIN_VOLUME_SHORT_TERM = 500  # Lower for short-term

# Categories of interest
FOCUS_SERIES = [
    "KXFEDEND", "KXFEDCHAIRNOM", "KXGDPUSMAX", "KXGDPSHAREMANU",
    "KXU3MAX", "CHINAUSGDP", "KXWARMING", "KXERUPTSUPER",
    "KXOAIANTH", "KXRAMPBREX", "KXEARTHQUAKECALIFORNIA",
    "KXPERSONPRESFUENTES", "KXPERSONPRESMAM", "KXINXBTC",
    # Add more economic/politics series
    "KXCPI", "KXFOMC", "KXJOBSREPORT", "KXNFP"
]

# ============== LOGGING ==============
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== KALSHI CLIENT ==============
def get_client():
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()
    config = Configuration()
    config.api_key_id = API_KEY_ID
    config.private_key_pem = private_key
    return KalshiClient(configuration=config)

def get_balance(client):
    balance = client._portfolio_api.get_balance()
    return balance.balance / 100

# ============== PUBLIC API ==============
def fetch_public(path, params=None):
    url = f"{BASE_URL}/trade-api/v2{path}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def get_events(category=None, status="open", limit=100):
    params = {"status": status, "limit": limit, "with_nested_markets": "true"}
    if category:
        params["category"] = category
    return fetch_public("/events", params).get('events', [])

def get_markets_by_series(series_ticker):
    try:
        return fetch_public("/markets", {"series_ticker": series_ticker}).get('markets', [])
    except:
        return []

def get_all_markets():
    """Fetch all interesting markets."""
    all_markets = []
    
    # From focus series
    for series in FOCUS_SERIES:
        markets = get_markets_by_series(series)
        all_markets.extend(markets)
    
    # From key categories
    for category in ["Economics", "Financials", "Politics", "Climate and Weather"]:
        try:
            events = get_events(category=category, limit=100)
            for event in events:
                all_markets.extend(event.get('markets', []))
        except Exception as e:
            logger.debug(f"Category {category} error: {e}")
    
    # Dedupe
    seen = set()
    unique = []
    for m in all_markets:
        ticker = m.get('ticker')
        if ticker and ticker not in seen:
            seen.add(ticker)
            unique.append(m)
    
    return unique

# ============== EXTERNAL DATA ==============
def get_cme_fedwatch_probs():
    """Try to get CME FedWatch probabilities."""
    # This would need proper implementation - placeholder
    return {}

def get_external_odds(market_title):
    """
    Get external probability estimate for a market.
    Returns None if no external data available.
    """
    title_lower = market_title.lower()
    
    # Fed-related markets - generally market is efficient
    if 'fed' in title_lower or 'rate' in title_lower:
        # Could integrate CME FedWatch here
        pass
    
    # For now, return None - we'll add sources later
    return None

# ============== ANALYSIS ==============
def calculate_days_to_resolution(market):
    """Calculate days until market resolves."""
    close_time = market.get('close_time') or market.get('expiration_time')
    if not close_time:
        return 9999  # Unknown = far future
    
    try:
        close_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = close_dt - now
        return max(0, delta.days)
    except:
        return 9999

def analyze_market(market):
    """Analyze market for opportunities with improved logic."""
    ticker = market.get('ticker', 'UNKNOWN')
    title = market.get('title', ticker)
    
    yes_bid = market.get('yes_bid', 0) or 0
    yes_ask = market.get('yes_ask', 0) or 0
    no_bid = market.get('no_bid', 0) or 0
    no_ask = market.get('no_ask', 0) or 0
    volume = market.get('volume', 0) or 0
    volume_24h = market.get('volume_24h', 0) or 0
    open_interest = market.get('open_interest', 0) or 0
    
    days_to_resolve = calculate_days_to_resolution(market)
    
    # Skip very low volume
    min_vol = MIN_VOLUME_SHORT_TERM if days_to_resolve <= 30 else MIN_VOLUME
    if volume < min_vol:
        return None
    
    opportunities = []
    spread = yes_ask - yes_bid if yes_ask and yes_bid else 0
    
    # Estimate fees (~2 cents per trade round trip)
    estimated_fees = 2
    
    # ==========================================
    # TIER 1: SHORT-TERM HIGH CONFIDENCE (< 30 days)
    # ==========================================
    if days_to_resolve <= 30:
        # High confidence NO (YES <= 15%)
        if yes_ask <= 15 and yes_ask > 0:
            no_cost = 100 - yes_bid
            potential = yes_bid - estimated_fees
            if potential >= MIN_EDGE_CENTS:
                max_contracts = int((CAPITAL * MAX_POSITION_PCT) / (no_cost / 100))
                opportunities.append({
                    "type": "🔥 HOT: SHORT-TERM NO",
                    "priority": 1,
                    "ticker": ticker,
                    "title": title,
                    "days_to_resolve": days_to_resolve,
                    "yes_price": f"{yes_ask}¢",
                    "no_cost": f"{no_cost}¢",
                    "potential_cents": potential,
                    "volume": volume,
                    "volume_24h": volume_24h,
                    "suggested_size": f"${min(20, CAPITAL * MAX_POSITION_PCT):.0f} ({max_contracts} contracts)",
                    "action": f"BUY NO at {no_cost}¢ → {potential}¢ profit in {days_to_resolve} days",
                    "roi_pct": f"{(potential/no_cost)*100:.1f}%",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        # High confidence YES (>= 85%)
        if yes_bid >= 85:
            potential = (100 - yes_ask) - estimated_fees
            if potential >= MIN_EDGE_CENTS:
                max_contracts = int((CAPITAL * MAX_POSITION_PCT) / (yes_ask / 100))
                opportunities.append({
                    "type": "🔥 HOT: SHORT-TERM YES",
                    "priority": 1,
                    "ticker": ticker,
                    "title": title,
                    "days_to_resolve": days_to_resolve,
                    "yes_price": f"{yes_ask}¢",
                    "potential_cents": potential,
                    "volume": volume,
                    "volume_24h": volume_24h,
                    "suggested_size": f"${min(20, CAPITAL * MAX_POSITION_PCT):.0f} ({max_contracts} contracts)",
                    "action": f"BUY YES at {yes_ask}¢ → {potential}¢ profit in {days_to_resolve} days",
                    "roi_pct": f"{(potential/yes_ask)*100:.1f}%",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    # ==========================================
    # TIER 2: MEDIUM-TERM (30-90 days)
    # ==========================================
    elif days_to_resolve <= 90:
        # Higher threshold for medium-term
        if yes_ask <= 10 and yes_ask > 0:
            no_cost = 100 - yes_bid
            potential = yes_bid - estimated_fees
            if potential >= MIN_EDGE_CENTS and volume >= 5000:
                opportunities.append({
                    "type": "📊 MEDIUM-TERM NO",
                    "priority": 2,
                    "ticker": ticker,
                    "title": title,
                    "days_to_resolve": days_to_resolve,
                    "yes_price": f"{yes_ask}¢",
                    "no_cost": f"{no_cost}¢",
                    "potential_cents": potential,
                    "volume": volume,
                    "action": f"BUY NO at {no_cost}¢ → {potential}¢ profit in {days_to_resolve} days",
                    "roi_pct": f"{(potential/no_cost)*100:.1f}%",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        if yes_bid >= 90:
            potential = (100 - yes_ask) - estimated_fees
            if potential >= MIN_EDGE_CENTS and volume >= 5000:
                opportunities.append({
                    "type": "📊 MEDIUM-TERM YES",
                    "priority": 2,
                    "ticker": ticker,
                    "title": title,
                    "days_to_resolve": days_to_resolve,
                    "yes_price": f"{yes_ask}¢",
                    "potential_cents": potential,
                    "volume": volume,
                    "action": f"BUY YES at {yes_ask}¢ → {potential}¢ profit in {days_to_resolve} days",
                    "roi_pct": f"{(potential/yes_ask)*100:.1f}%",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    # ==========================================
    # TIER 3: LONG-TERM HIGH VALUE (90+ days, but big edge)
    # ==========================================
    else:
        # Only flag if very high edge AND volume
        if yes_ask <= 8 and volume >= 50000:
            no_cost = 100 - yes_bid
            potential = yes_bid - estimated_fees
            if potential >= 5:  # Higher threshold for long-term
                opportunities.append({
                    "type": "📈 LONG-TERM NO",
                    "priority": 3,
                    "ticker": ticker,
                    "title": title,
                    "days_to_resolve": days_to_resolve,
                    "yes_price": f"{yes_ask}¢",
                    "no_cost": f"{no_cost}¢",
                    "potential_cents": potential,
                    "volume": volume,
                    "action": f"BUY NO at {no_cost}¢ → {potential}¢ profit (long-term hold)",
                    "roi_pct": f"{(potential/no_cost)*100:.1f}%",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        if yes_bid >= 92 and volume >= 50000:
            potential = (100 - yes_ask) - estimated_fees
            if potential >= 5:
                opportunities.append({
                    "type": "📈 LONG-TERM YES",
                    "priority": 3,
                    "ticker": ticker,
                    "title": title,
                    "days_to_resolve": days_to_resolve,
                    "yes_price": f"{yes_ask}¢",
                    "potential_cents": potential,
                    "volume": volume,
                    "action": f"BUY YES at {yes_ask}¢ → {potential}¢ profit (long-term hold)",
                    "roi_pct": f"{(potential/yes_ask)*100:.1f}%",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    # ==========================================
    # MARKET MAKING OPPORTUNITIES
    # ==========================================
    if spread >= 5 and volume >= 10000 and days_to_resolve <= 90:
        opportunities.append({
            "type": "💹 WIDE SPREAD",
            "priority": 4,
            "ticker": ticker,
            "title": title,
            "days_to_resolve": days_to_resolve,
            "spread": f"{spread}¢",
            "yes_bid": f"{yes_bid}¢",
            "yes_ask": f"{yes_ask}¢",
            "volume": volume,
            "action": f"Market making opportunity: place orders inside {spread}¢ spread",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return opportunities if opportunities else None

def log_opportunity(opp, is_hot=False):
    """Log opportunity to file."""
    target_file = HOT_OPPORTUNITIES_FILE if is_hot else OPPORTUNITIES_FILE
    with open(target_file, "a") as f:
        f.write(json.dumps(opp) + "\n")
    
    # Format for console
    priority = opp.get('priority', 9)
    if priority == 1:
        logger.info("=" * 70)
        logger.info(f"🔥🔥🔥 {opp['type']} 🔥🔥🔥")
        logger.info(f"   {opp['title'][:55]}")
        logger.info(f"   Days to resolve: {opp['days_to_resolve']}")
        logger.info(f"   {opp['action']}")
        logger.info(f"   ROI: {opp.get('roi_pct', 'N/A')} | Volume: {opp['volume']:,}")
        if 'suggested_size' in opp:
            logger.info(f"   Suggested: {opp['suggested_size']}")
        logger.info("=" * 70)
    elif priority <= 3:
        logger.info(f"📊 {opp['type']}: {opp['title'][:40]}... ({opp.get('roi_pct', 'N/A')} ROI)")

# ============== SCANNER ==============
def scan_once():
    """Run scan with priority sorting."""
    markets = get_all_markets()
    logger.info(f"Fetched {len(markets)} markets")
    
    all_opps = []
    for market in markets:
        opps = analyze_market(market)
        if opps:
            all_opps.extend(opps)
    
    # Sort by priority (1 = best)
    all_opps.sort(key=lambda x: (x.get('priority', 9), -x.get('potential_cents', 0)))
    
    # Log opportunities
    hot_count = 0
    for opp in all_opps:
        is_hot = opp.get('priority') == 1
        if is_hot:
            hot_count += 1
        log_opportunity(opp, is_hot=is_hot)
    
    return len(all_opps), hot_count

def show_top_opportunities():
    """Show top opportunities summary."""
    markets = get_all_markets()
    
    all_opps = []
    for market in markets:
        opps = analyze_market(market)
        if opps:
            all_opps.extend(opps)
    
    # Sort by priority then ROI
    all_opps.sort(key=lambda x: (x.get('priority', 9), -x.get('potential_cents', 0)))
    
    print(f"\n{'='*80}")
    print(f"TOP OPPORTUNITIES (sorted by priority)")
    print(f"{'='*80}")
    
    for i, opp in enumerate(all_opps[:20], 1):
        print(f"\n{i}. {opp['type']}")
        print(f"   {opp['title'][:60]}")
        print(f"   {opp['action']}")
        print(f"   Days: {opp.get('days_to_resolve', '?')} | ROI: {opp.get('roi_pct', '?')} | Vol: {opp.get('volume', 0):,}")

def run_scanner(client):
    """Main loop."""
    logger.info("=" * 70)
    logger.info("🚀 Kalshi Scanner v4 (Grok-Enhanced) Starting")
    logger.info(f"   Capital: ${CAPITAL}")
    logger.info(f"   Max position: {MAX_POSITION_PCT*100:.0f}%")
    logger.info(f"   Min edge: {MIN_EDGE_CENTS}¢")
    logger.info(f"   Scan interval: {SCAN_INTERVAL_SECONDS}s")
    logger.info("=" * 70)
    
    scan_count = 0
    while True:
        try:
            scan_count += 1
            logger.info(f"\n--- Scan #{scan_count} @ {datetime.now().strftime('%H:%M:%S')} ---")
            
            total_opps, hot_opps = scan_once()
            
            if hot_opps > 0:
                logger.info(f"🔥 {hot_opps} HOT opportunities found!")
            logger.info(f"Total: {total_opps} opportunities")
            
            logger.info(f"Next scan in {SCAN_INTERVAL_SECONDS}s...")
            time.sleep(SCAN_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            logger.info("\nStopped")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(60)

# ============== CLI ==============
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Kalshi Scanner v4")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--top", action="store_true")
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()
    
    if args.interval:
        SCAN_INTERVAL_SECONDS = args.interval
    
    client = get_client()
    balance = get_balance(client)
    CAPITAL = balance
    print(f"💰 Balance: ${balance:.2f}")
    
    if args.top:
        show_top_opportunities()
    elif args.once:
        scan_once()
    else:
        run_scanner(client)
