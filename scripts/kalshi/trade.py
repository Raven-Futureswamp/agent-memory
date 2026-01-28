#!/usr/bin/env python3
"""
Kalshi Trading Module
Place orders on Kalshi markets.
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from kalshi_python import KalshiClient, Configuration, CreateOrderRequest

# ============== CONFIG ==============
API_KEY_ID = os.getenv("KALSHI_API_KEY_ID", "898f7406-b498-4205-8949-c9f137403966")
PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", str(PROJECT_ROOT / ".kalshi-private-key.pem"))

def get_client():
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()
    config = Configuration()
    config.api_key_id = API_KEY_ID
    config.private_key_pem = private_key
    return KalshiClient(configuration=config)

def get_balance(client):
    balance = client._portfolio_api.get_balance()
    return balance.balance  # in cents

def get_positions(client):
    """Get current positions."""
    try:
        positions = client._portfolio_api.get_positions()
        return positions.market_positions if hasattr(positions, 'market_positions') else []
    except Exception as e:
        print(f"Error getting positions: {e}")
        return []

def get_market(client, ticker):
    """Get market details."""
    try:
        market = client._markets_api.get_market(ticker=ticker)
        return market.market if hasattr(market, 'market') else market
    except Exception as e:
        print(f"Error getting market {ticker}: {e}")
        return None

def place_order(client, ticker, side, count, limit_price=None):
    """
    Place an order.
    side: 'yes' or 'no'
    count: number of contracts
    limit_price: price in cents (optional, market order if None)
    """
    try:
        # Build order request
        order = CreateOrderRequest(
            ticker=ticker,
            side=side,
            count=count,
            type='limit' if limit_price else 'market',
            action='buy',
        )
        
        if limit_price:
            order.yes_price = limit_price if side == 'yes' else None
            order.no_price = limit_price if side == 'no' else None
        
        response = client._portfolio_api.create_order(**order.model_dump(exclude_none=True))
        return response
    except Exception as e:
        print(f"Error placing order: {e}")
        return None

def show_portfolio(client):
    """Display current portfolio."""
    balance = get_balance(client)
    positions = get_positions(client)
    
    print(f"\n💰 Balance: ${balance/100:.2f}")
    print(f"📊 Positions: {len(positions)}")
    
    if positions:
        print("\nOpen Positions:")
        for p in positions:
            ticker = getattr(p, 'ticker', 'Unknown')
            pos = getattr(p, 'position', 0)
            side = 'YES' if pos > 0 else 'NO'
            count = abs(pos)
            print(f"  {ticker}: {count} {side}")
    
    return balance, positions

if __name__ == "__main__":
    client = get_client()
    show_portfolio(client)
