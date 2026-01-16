#!/usr/bin/env bash
# Phase-A.1 Kernel Pulse Verification Script
# Verifies /kernel/pulse/summary/ endpoint against Pulse ABI v0.1

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Phase-A.1 Kernel Pulse — Acceptance Verification      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check TOKEN
if [ -z "${TOKEN:-}" ]; then
  echo "❌ ERROR: TOKEN not set"
  echo ""
  echo "Please export your JWT token first:"
  echo ""
  echo "  export TOKEN=\"eyJhbGci...\""
  echo ""
  echo "Or get a new token:"
  echo ""
  echo "  curl -X POST $BACKEND_URL/api/v1/users/login/ \\"
  echo "    -H \"Content-Type: application/json\" \\"
  echo "    -d '{\"identifier\":\"SUPERUSER\",\"password\":\"PASSWORD\"}' | jq -r '.access'"
  echo ""
  exit 1
fi

echo "🔑 Token: ${TOKEN:0:20}..."
echo ""

# Make request
echo "📡 GET $BACKEND_URL/kernel/pulse/summary/"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/kernel/pulse/summary/")

HTTP_STATUS=$(echo "$RESPONSE" | grep -o 'HTTP_STATUS:[0-9]*' | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')

# Check HTTP status
if [ "$HTTP_STATUS" != "200" ]; then
  echo "❌ FAILED: HTTP $HTTP_STATUS"
  echo ""
  echo "Response:"
  echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
  exit 1
fi

echo "✅ HTTP 200 OK"
echo ""

# Validate JSON
if ! echo "$BODY" | jq . > /dev/null 2>&1; then
  echo "❌ FAILED: Invalid JSON response"
  echo "$BODY"
  exit 1
fi

echo "✅ Valid JSON"
echo ""

# Check Pulse ABI v0.1 keys
echo "🔍 Validating Pulse ABI v0.1 contract..."
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

check_key() {
  KEY=$1
  if echo "$BODY" | jq -e ".$KEY" > /dev/null 2>&1; then
    echo "  ✅ $KEY"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "  ❌ $KEY (MISSING)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
}

check_nested_key() {
  KEY=$1
  if echo "$BODY" | jq -e "$KEY" > /dev/null 2>&1; then
    echo "  ✅ $KEY"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "  ❌ $KEY (MISSING)"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
}

# Top-level keys
check_key "pulse_version"
check_key "now"
check_key "kernel_state"
check_key "recent_syscalls"
check_key "counts"
check_key "active_locks"
check_key "top_errors_24h"

# kernel_state keys
check_nested_key ".kernel_state.mode"
check_nested_key ".kernel_state.active_lock_pressure"
check_nested_key ".kernel_state.error_rate_1h"
check_nested_key ".kernel_state.chaos_safe"

# counts keys
check_nested_key ".counts.last_1h"
check_nested_key ".counts.last_24h"

# active_locks keys
check_nested_key ".active_locks.count"
check_nested_key ".active_locks.samples"

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Checks: $CHECKS_PASSED passed, $CHECKS_FAILED failed"
echo "─────────────────────────────────────────────────────────────"
echo ""

if [ $CHECKS_FAILED -gt 0 ]; then
  echo "❌ ABI validation FAILED"
  exit 1
fi

# Verify pulse_version
PULSE_VERSION=$(echo "$BODY" | jq -r '.pulse_version')
if [ "$PULSE_VERSION" != "0.1" ]; then
  echo "❌ FAILED: pulse_version must be '0.1', got '$PULSE_VERSION'"
  exit 1
fi

echo "✅ pulse_version: 0.1"
echo ""

# Display summary
echo "📊 Kernel State Summary:"
echo "────────────────────────────────────────────────────────────"
MODE=$(echo "$BODY" | jq -r '.kernel_state.mode')
PRESSURE=$(echo "$BODY" | jq -r '.kernel_state.active_lock_pressure')
ERROR_RATE=$(echo "$BODY" | jq -r '.kernel_state.error_rate_1h')
CHAOS_SAFE=$(echo "$BODY" | jq -r '.kernel_state.chaos_safe')

echo "  Mode:          $MODE"
echo "  Lock Pressure: $PRESSURE"
echo "  Error Rate:    $ERROR_RATE"
echo "  Chaos Safe:    $CHAOS_SAFE"
echo ""

TOTAL_1H=$(echo "$BODY" | jq -r '.counts.last_1h.total')
SUCCESS_1H=$(echo "$BODY" | jq -r '.counts.last_1h.success')
TOTAL_24H=$(echo "$BODY" | jq -r '.counts.last_24h.total')

echo "📈 Activity Summary:"
echo "────────────────────────────────────────────────────────────"
echo "  Last 1h:  $TOTAL_1H syscalls ($SUCCESS_1H success)"
echo "  Last 24h: $TOTAL_24H syscalls"
echo ""

ACTIVE_LOCKS=$(echo "$BODY" | jq -r '.active_locks.count')
TOP_ERRORS=$(echo "$BODY" | jq -r '.top_errors_24h | length')

echo "🔒 Active Locks: $ACTIVE_LOCKS"
echo "⚠️  Top Errors:   $TOP_ERRORS unique error types"
echo ""

# Full response
echo "📄 Full Response:"
echo "────────────────────────────────────────────────────────────"
echo "$BODY" | jq .
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Phase-A.1 Acceptance: PASSED              ║"
echo "╚════════════════════════════════════════════════════════════╝"
