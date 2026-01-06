#!/bin/bash

# GateAI Kernel Chaos Demo
# Scenarios: Idempotency, Resource War, Atomic Trap

BASE_URL=${BASE_URL:-"http://localhost:8001"}
DISPATCH_URL="$BASE_URL/kernel/dispatch"
TRAP_URL="$BASE_URL/kernel/sandbox/atomic-trap"

get_future_date() {
    if date -v+1H >/dev/null 2>&1; then
        date -u -v+1H '+%Y-%m-%dT%H:%M:%SZ'
    else
        date -u -d '+1 hour' '+%Y-%m-%dT%H:%M:%SZ'
    fi
}

run_dispatch() {
    local scenario="$1"
    local trace_id="$2"
    local payload="$3"
    local url="${4:-$DISPATCH_URL}"

    local res=$(curl -s -i -X POST "$url" \
      -H "Content-Type: application/json" \
      -H "X-GateAI-TraceID: $trace_id" \
      -d "$payload")
    
    local status=$(echo "$res" | grep HTTP | awk '{print $2}')
    local body=$(echo "$res" | sed -n '/{/,$p')
    local outcome=$(echo "$body" | grep -o '"outcome_code": "[^"]*"' | cut -d'"' -f4)
    
    printf "%-12s | %-4s | %-16s | %s\n" "$scenario" "$status" "$outcome" "$trace_id"
    echo "$outcome" > "/tmp/outcome_${trace_id}"
}

echo "Starting Chaos Demo..."
echo "--------------------------------------------------------------------------------"
printf "%-12s | %-4s | %-16s | %s\n" "SCENARIO" "HTTP" "OUTCOME" "TRACE_ID"
echo "--------------------------------------------------------------------------------"

# --- Scenario A: The Loyal Re-entry ---
EXPIRES_A=$(get_future_date)
PAYLOAD_A=$(cat <<EOF
{
  "syscall_name": "sys_claim",
  "payload": {
    "decision_id": "dec-chaos-A",
    "context_hash": "ctx-chaos-A",
    "resource_type": "demo",
    "resource_id": 101,
    "owner_id": 101,
    "expires_at": "$EXPIRES_A"
  }
}
EOF
)
run_dispatch "Scenario A1" "chaos-A-1" "$PAYLOAD_A"
run_dispatch "Scenario A2" "chaos-A-2" "$PAYLOAD_A"

# --- Scenario B: The Resource War ---
EXPIRES_B=$(get_future_date)
for i in {1..5}; do
    PAYLOAD_B=$(cat <<EOF
{
  "syscall_name": "sys_claim",
  "payload": {
    "decision_id": "dec-war-$i",
    "context_hash": "ctx-war-$i",
    "resource_type": "demo",
    "resource_id": 99,
    "owner_id": $((200 + i)),
    "expires_at": "$EXPIRES_B"
  }
}
EOF
)
    run_dispatch "Scenario B$i" "chaos-B-$i" "$PAYLOAD_B" &
done
wait

# Scenario B aggregation
COUNT_OK=$(cat /tmp/outcome_chaos-B-* 2>/dev/null | grep -cx "OK" || echo 0)
COUNT_CONFLICT=$(cat /tmp/outcome_chaos-B-* 2>/dev/null | grep -cx "CONFLICT" || echo 0)

# --- Scenario C: The Atomic Trap ---
# Note: Payload for trap often needs to overlap with something existing or follow logic.
# For simplicity, we just trigger the endpoint which handles the setup.
PAYLOAD_C='{"resource_id": 999}'
run_dispatch "Scenario C" "chaos-C-1" "$PAYLOAD_C" "$TRAP_URL"

echo "--------------------------------------------------------------------------------"
echo "Chaos Aggregation (Scenario B): OK=$COUNT_OK, CONFLICT=$COUNT_CONFLICT"

# Validation
ERROR=0
if [[ "$(cat /tmp/outcome_chaos-A-1)" != "OK" ]]; then echo "ERROR: Scenario A1 failed"; ERROR=1; fi
if [[ "$(cat /tmp/outcome_chaos-A-2)" != "REPLAY" ]]; then echo "ERROR: Scenario A2 failed"; ERROR=1; fi
if [[ $COUNT_OK -ne 1 || $COUNT_CONFLICT -ne 4 ]]; then echo "ERROR: Scenario B failed (Expected 1 OK, 4 CONFLICT)"; ERROR=1; fi
if [[ "$(cat /tmp/outcome_chaos-C-1)" != "FAILED_RETRYABLE" ]]; then echo "ERROR: Scenario C failed"; ERROR=1; fi

rm /tmp/outcome_chaos-*
exit $ERROR
