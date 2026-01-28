#!/bin/bash
# Raven Trading System - Trade Executor
# Usage: ./trade.sh buy|sell SYMBOL AMOUNT
#   AMOUNT can be dollar amount or share quantity

source /Users/studiomac/clawd/.env

ACTION=$1
SYMBOL=$2
AMOUNT=$3

API_KEY="$ALPACA_API_KEY"
SECRET_KEY="$ALPACA_SECRET_KEY"
BASE_URL="$ALPACA_BASE_URL"

if [ -z "$ACTION" ] || [ -z "$SYMBOL" ] || [ -z "$AMOUNT" ]; then
  echo "Usage: ./trade.sh buy|sell SYMBOL AMOUNT"
  echo "  AMOUNT: Use $ prefix for dollar amount (e.g., \$50)"
  echo "          Use number for share quantity (e.g., 10)"
  exit 1
fi

# Determine if notional (dollar) or qty (shares)
if [[ $AMOUNT == \$* ]]; then
  NOTIONAL="${AMOUNT:1}"
  ORDER_TYPE="notional"
  echo "📊 Placing $ACTION order for \$$NOTIONAL of $SYMBOL..."
  
  ORDER=$(curl -s -X POST "$BASE_URL/v2/orders" \
    -H "APCA-API-KEY-ID: $API_KEY" \
    -H "APCA-API-SECRET-KEY: $SECRET_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"symbol\": \"$SYMBOL\",
      \"notional\": \"$NOTIONAL\",
      \"side\": \"$ACTION\",
      \"type\": \"market\",
      \"time_in_force\": \"day\"
    }")
else
  QTY="$AMOUNT"
  ORDER_TYPE="qty"
  echo "📊 Placing $ACTION order for $QTY shares of $SYMBOL..."
  
  ORDER=$(curl -s -X POST "$BASE_URL/v2/orders" \
    -H "APCA-API-KEY-ID: $API_KEY" \
    -H "APCA-API-SECRET-KEY: $SECRET_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"symbol\": \"$SYMBOL\",
      \"qty\": \"$QTY\",
      \"side\": \"$ACTION\",
      \"type\": \"market\",
      \"time_in_force\": \"day\"
    }")
fi

# Check result
STATUS=$(echo $ORDER | jq -r '.status // .message // "unknown"')
ORDER_ID=$(echo $ORDER | jq -r '.id // "N/A"')

if [ "$STATUS" == "accepted" ] || [ "$STATUS" == "pending_new" ] || [ "$STATUS" == "new" ]; then
  echo "✅ Order placed successfully!"
  echo "   Order ID: $ORDER_ID"
  echo "   Status: $STATUS"
else
  echo "❌ Order failed!"
  echo "   Response: $ORDER"
fi
