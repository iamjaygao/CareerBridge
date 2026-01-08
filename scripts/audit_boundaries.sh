#!/usr/bin/env bash
set -euo pipefail

echo "=== GateAI Boundary Audit ==="
echo ""

# Helper: run grep, but do not fail the script when matches exist
run_grep() {
  local title="$1"
  shift
  echo ">>> $title"
  # shellcheck disable=SC2068
  if grep -RIn --exclude-dir=.git --exclude-dir=venv --exclude-dir=node_modules --exclude=*.pyc --exclude=*.log ${@}; then
    echo ""
  else
    echo "(no matches)"
    echo ""
  fi
}

# 1) Kernel must NOT import app/business modules
run_grep "[KERNEL -> APP imports] gateai/kernel importing app modules" \
  gateai/kernel \
  -e "from gateai\.appointments" \
  -e "import gateai\.appointments" \
  -e "from gateai\.payments" \
  -e "import gateai\.payments" \
  -e "from gateai\.human_loop" \
  -e "import gateai\.human_loop" \
  -e "from gateai\.ats_signals" \
  -e "import gateai\.ats_signals" \
  -e "from gateai\.mentors" \
  -e "import gateai\.mentors"

# 2) App must NOT import kernel internals directly
run_grep "[APP -> KERNEL internal imports] app modules importing gateai/kernel" \
  gateai/appointments gateai/payments gateai/human_loop gateai/ats_signals gateai/chat gateai/dashboard gateai/adminpanel \
  -e "from gateai\.kernel" \
  -e "import gateai\.kernel" \
  -e "from gateai\.kernel\.syscalls" \
  -e "import gateai\.kernel\.syscalls"

# 3) Forbidden direct state mutations (reservation + appointment status)
run_grep "[FORBIDDEN writes] reserved_until / reserved_appointment" \
  gateai \
  -e "reserved_until" \
  -e "reserved_appointment"

run_grep "[FORBIDDEN writes] appointment\\.status assignments (heuristic scan)" \
  gateai \
  -e "appointment\.status\s*=" \
  -e "Appointment\.status\s*="

# 4) ResourceLock direct usage outside kernel/interface
# (We allow it inside gateai/kernel, gateai/decision_slots/models.py, gateai/kernel/agent_sdk.py, gateai/gateai/kernel_events.py)
run_grep "[ResourceLock usage] check for direct imports/usages" \
  gateai \
  -e "ResourceLock"

echo "=== Audit complete ==="
