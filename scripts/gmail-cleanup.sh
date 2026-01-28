#!/bin/bash
# Gmail Cleanup Script - Archives old emails in batches
export GOG_KEYRING_PASSWORD="raven2026"
export GOG_ACCOUNT="brownjeshua@gmail.com"

QUERY="$1"
TOTAL=0
ROUNDS=0
MAX_ROUNDS=${2:-100}  # default 100 rounds of 50 = 5000 messages

echo "Starting cleanup: $QUERY"
echo "Max rounds: $MAX_ROUNDS"

while [ $ROUNDS -lt $MAX_ROUNDS ]; do
    # Get batch of message IDs (always first page since we're removing them)
    IDS=$(gog gmail messages search "$QUERY" --max 50 --plain 2>&1 | tail -n +2 | grep -v '^#' | awk -F'\t' '{print $1}')
    COUNT=$(echo "$IDS" | grep -c '[a-f0-9]')

    if [ "$COUNT" -eq 0 ]; then
        echo "No more messages found."
        break
    fi

    # Archive batch
    IDS_INLINE=$(echo "$IDS" | tr '\n' ' ')
    gog gmail batch modify $IDS_INLINE --remove INBOX,UNREAD --force --no-input 2>&1
    
    TOTAL=$((TOTAL + COUNT))
    ROUNDS=$((ROUNDS + 1))
    echo "Round $ROUNDS: Archived $COUNT | Total: $TOTAL"
    
    sleep 0.5
done

echo "Done! Total archived: $TOTAL"
