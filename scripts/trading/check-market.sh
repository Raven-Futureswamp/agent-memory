#!/bin/bash
# Raven Trading System - Market Check
# Run during market hours to scan for opportunities

source /Users/studiomac/clawd/.env

API_KEY="$ALPACA_API_KEY"
SECRET_KEY="$ALPACA_SECRET_KEY"
BASE_URL="$ALPACA_BASE_URL"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  RAVEN TRADING SYSTEM - Market Scan"
echo "  $(date)"
echo "=========================================="
echo ""

# Check account
echo "📊 Account Status:"
ACCOUNT=$(curl -s "$BASE_URL/v2/account" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY")

CASH=$(echo $ACCOUNT | jq -r '.cash')
BUYING_POWER=$(echo $ACCOUNT | jq -r '.buying_power')
EQUITY=$(echo $ACCOUNT | jq -r '.equity')

echo "   Cash: \$$CASH"
echo "   Buying Power: \$$BUYING_POWER"
echo "   Equity: \$$EQUITY"
echo ""

# Check positions
echo "📈 Current Positions:"
POSITIONS=$(curl -s "$BASE_URL/v2/positions" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY")

if [ "$POSITIONS" == "[]" ]; then
  echo "   No open positions"
else
  echo "$POSITIONS" | jq -r '.[] | "   \(.symbol): \(.qty) shares @ $\(.avg_entry_price) | P/L: $\(.unrealized_pl)"'
fi
echo ""

# Get snapshots for watchlist
WATCHLIST="NVDA,TSLA,AMD,META,PLTR,SOFI,SPY,QQQ"
echo "👀 Watchlist Prices:"
SNAPSHOTS=$(curl -s "https://data.alpaca.markets/v2/stocks/snapshots?symbols=$WATCHLIST" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY")

for SYMBOL in $(echo $WATCHLIST | tr ',' ' '); do
  PRICE=$(echo $SNAPSHOTS | jq -r ".[\"$SYMBOL\"].latestTrade.p // \"N/A\"")
  PREV_CLOSE=$(echo $SNAPSHOTS | jq -r ".[\"$SYMBOL\"].prevDailyBar.c // \"N/A\"")
  
  if [ "$PRICE" != "N/A" ] && [ "$PREV_CLOSE" != "N/A" ]; then
    CHANGE=$(echo "scale=2; (($PRICE - $PREV_CLOSE) / $PREV_CLOSE) * 100" | bc 2>/dev/null || echo "N/A")
    if [ "$CHANGE" != "N/A" ]; then
      if (( $(echo "$CHANGE > 0" | bc -l) )); then
        echo -e "   $SYMBOL: \$${PRICE} ${GREEN}+${CHANGE}%${NC}"
      else
        echo -e "   $SYMBOL: \$${PRICE} ${RED}${CHANGE}%${NC}"
      fi
    else
      echo "   $SYMBOL: \$${PRICE}"
    fi
  else
    echo "   $SYMBOL: \$${PRICE}"
  fi
done

echo ""
echo "=========================================="
