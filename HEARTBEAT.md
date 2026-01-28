# HEARTBEAT.md

## Session Health Check
Run: `bash /Users/studiomac/clawd/scripts/session-health.sh`

If output contains "CRITICAL" or "WARNING":
- CRITICAL (orphaned tool_results): Alert Jess immediately via iMessage. Session corruption detected — needs manual fix.
- WARNING (large session): Note it but don't alert unless >20MB.

If output is "OK": No action needed, reply HEARTBEAT_OK.
