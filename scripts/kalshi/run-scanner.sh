#!/bin/bash
# Run Kalshi scanner continuously
# Usage: ./run-scanner.sh [--interval SECONDS]

cd /Users/studiomac/clawd
source .venv/bin/activate

# Default 5 minute interval
INTERVAL=${1:-300}

echo "Starting Kalshi Scanner (interval: ${INTERVAL}s)"
echo "Logs: logs/kalshi/scanner.log"
echo "Opportunities: logs/kalshi/opportunities.jsonl"
echo ""

python3 scripts/kalshi/scanner.py --interval "$INTERVAL"
