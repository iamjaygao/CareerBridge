#!/bin/bash

# GateAI Kernel: Happy Path + Idempotency Demo
# Goal: Prove contract-correct OK then REPLAY.

BASE_URL=${BASE_URL:-"http://localhost:8001"}
ENDPOINT="$BASE_URL/kernel/dispatch"

# Helper for portable future date (ISO8601 Z)
get_future_date() {
    if date -v+1H >/dev/null 2>&1; then
        # macOS
        date -u -v+1H '+%Y-%m-%dT%H:%M:%SZ'
    else
        # GNU/Linux
        date -u -d '+1 hour' '+%Y-%m-%dT%H:%M:%SZ'
    fi
}

DECISION_ID="dec-demo-001"
CONTEXT_HASH="ctx-demo-001"
EXPIRES_AT=$(get_future_date)

echo "--------------------------------------------------"
echo "STEP 1: FIRST CLAIM (Expect OK)"
echo "--------------------------------------------------"

PAYLOAD=$(cat <<EOF
{
  "syscall_name": "sys_claim",
  "payload": {
    "decision_id": "$DECISION_ID",
    "context_hash": "$CONTEXT_HASH",
    "resource_type": "demo",
    "resource_id": 42,
    "owner_id": 10,
    "expires_at": "$EXPIRES_AT"
  }
}
EOF
)

RESPONSE_1=$(curl -s -i -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-GateAI-TraceID: demo-ok-1" \
  -d "$PAYLOAD")

STATUS_1=$(echo "$RESPONSE_1" | grep HTTP | awk '{print $2}')
BODY_1=$(echo "$RESPONSE_1" | sed -n '/{/,$p')
OUTCOME_1=$(echo "$BODY_1" | grep -o '"outcome_code": "[^"]*"' | cut -d'"' -f4)

echo "HTTP Status: $STATUS_1"
echo "Response: $BODY_1"

if [[ "$STATUS_1" != "200" || "$OUTCOME_1" != "OK" ]]; then
    echo "FAILED: Expected 200 OK, got $STATUS_1 $OUTCOME_1"
    exit 1
fi

echo -e "\n--------------------------------------------------"
echo "STEP 2: REPLAY CLAIM (Expect REPLAY)"
echo "--------------------------------------------------"

RESPONSE_2=$(curl -s -i -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-GateAI-TraceID: demo-ok-2" \
  -d "$PAYLOAD")

STATUS_2=$(echo "$RESPONSE_2" | grep HTTP | awk '{print $2}')
BODY_2=$(echo "$RESPONSE_2" | sed -n '/{/,$p')
OUTCOME_2=$(echo "$BODY_2" | grep -o '"outcome_code": "[^"]*"' | cut -d'"' -f4)

echo "HTTP Status: $STATUS_2"
echo "Response: $BODY_2"

if [[ "$STATUS_2" != "200" || "$OUTCOME_2" != "REPLAY" ]]; then
    echo "FAILED: Expected 200 REPLAY, got $STATUS_2 $OUTCOME_2"
    exit 1
fi

echo -e "\nSUCCESS: Idempotency contract verified."
