#!/bin/bash
# Session Health Check
# Detects orphaned tool_result blocks that can corrupt sessions

SESSION_DIR="$HOME/.clawdbot/agents/main/sessions"
MAIN_SESSION=$(cat "$SESSION_DIR/sessions.json" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'agent:main:main' in data:
        print(data['agent:main:main'].get('sessionId', ''))
except:
    pass
" 2>/dev/null)

if [ -z "$MAIN_SESSION" ]; then
    echo "OK: No active main session"
    exit 0
fi

SESSION_FILE="$SESSION_DIR/$MAIN_SESSION.jsonl"

if [ ! -f "$SESSION_FILE" ]; then
    echo "OK: Session file not found (fresh start)"
    exit 0
fi

# Check session size (warn if > 10MB)
SIZE=$(stat -f%z "$SESSION_FILE" 2>/dev/null || stat -c%s "$SESSION_FILE" 2>/dev/null)
SIZE_MB=$((SIZE / 1024 / 1024))

if [ "$SIZE_MB" -gt 10 ]; then
    echo "WARNING: Session file is ${SIZE_MB}MB (consider rotating)"
fi

# Check for orphaned tool_results
python3 - "$SESSION_FILE" << 'PYEOF'
import json
import sys

session_file = sys.argv[1] if len(sys.argv) > 1 else ""
if not session_file:
    print("OK: No session to check")
    sys.exit(0)

try:
    tool_uses = set()
    tool_results = set()
    
    with open(session_file, 'r') as f:
        for line in f:
            try:
                msg = json.loads(line)
                content = msg.get('message', {}).get('content', [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get('type') == 'tool_use':
                                tool_uses.add(block.get('id', ''))
                            elif block.get('type') == 'tool_result':
                                tool_results.add(block.get('tool_use_id', ''))
            except:
                pass
    
    orphaned = tool_results - tool_uses
    if orphaned:
        print(f"CRITICAL: Found {len(orphaned)} orphaned tool_result(s)")
        print(f"IDs: {list(orphaned)[:3]}...")
        sys.exit(2)
    else:
        print("OK: No orphaned tool_results detected")
        sys.exit(0)
        
except Exception as e:
    print(f"ERROR: Could not check session: {e}")
    sys.exit(1)
PYEOF
