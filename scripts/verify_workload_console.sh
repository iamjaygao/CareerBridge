#!/bin/bash

##
## Workload Runtime Console Verification Script
##
## Verifies Phase-A.2 implementation is complete and working
##

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔍 Verifying Phase-A.2 Workload Runtime Console..."
echo ""

# Check 1: Scanner script exists
echo "✓ Check 1: Scanner script exists"
if [[ ! -f "$PROJECT_ROOT/scripts/build_frozen_registry.mjs" ]]; then
  echo "❌ FAIL: build_frozen_registry.mjs not found"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 2: Sync script exists
echo "✓ Check 2: Sync script exists"
if [[ ! -f "$PROJECT_ROOT/scripts/sync_registry_to_frontend.sh" ]]; then
  echo "❌ FAIL: sync_registry_to_frontend.sh not found"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 3: Test script exists
echo "✓ Check 3: Test script exists"
if [[ ! -f "$PROJECT_ROOT/scripts/test_frozen_registry.mjs" ]]; then
  echo "❌ FAIL: test_frozen_registry.mjs not found"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 4: Run scanner
echo "✓ Check 4: Run scanner"
node "$PROJECT_ROOT/scripts/build_frozen_registry.mjs" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
  echo "❌ FAIL: Scanner failed"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 5: Registry file exists
echo "✓ Check 5: Registry file exists"
if [[ ! -f "$PROJECT_ROOT/docs/WORKLOAD_FROZEN_REGISTRY.json" ]]; then
  echo "❌ FAIL: Registry not generated"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 6: Run registry tests
echo "✓ Check 6: Run registry tests"
node "$PROJECT_ROOT/scripts/test_frozen_registry.mjs" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
  echo "❌ FAIL: Registry tests failed"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 7: Sync to frontend
echo "✓ Check 7: Sync to frontend"
"$PROJECT_ROOT/scripts/sync_registry_to_frontend.sh" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
  echo "❌ FAIL: Sync failed"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 8: Frontend registry exists
echo "✓ Check 8: Frontend registry exists"
if [[ ! -f "$PROJECT_ROOT/frontend/public/registry/WORKLOAD_FROZEN_REGISTRY.json" ]]; then
  echo "❌ FAIL: Frontend registry not found"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 9: Frontend page exists
echo "✓ Check 9: Frontend page exists"
if [[ ! -f "$PROJECT_ROOT/frontend/src/pages/superadmin/WorkloadRuntimeConsolePage.tsx" ]]; then
  echo "❌ FAIL: Console page not found"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 10: Frontend test exists
echo "✓ Check 10: Frontend test exists"
if [[ ! -f "$PROJECT_ROOT/frontend/src/pages/superadmin/__tests__/WorkloadRuntimeConsolePage.test.tsx" ]]; then
  echo "❌ FAIL: Frontend test not found"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 11: Route in App.tsx
echo "✓ Check 11: Route in App.tsx"
if ! grep -q "WorkloadRuntimeConsolePage" "$PROJECT_ROOT/frontend/src/App.tsx"; then
  echo "❌ FAIL: Route not found in App.tsx"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Check 12: Sidebar menu item
echo "✓ Check 12: Sidebar menu item"
if ! grep -q "Workload Runtime Console" "$PROJECT_ROOT/frontend/src/components/layout/SuperAdminSidebar.tsx"; then
  echo "❌ FAIL: Menu item not found in sidebar"
  exit 1
fi
echo "  ✅ PASS"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All checks passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Registry Summary:"
node -e "const fs = require('fs'); const r = JSON.parse(fs.readFileSync('$PROJECT_ROOT/docs/WORKLOAD_FROZEN_REGISTRY.json', 'utf8')); console.log('  - Version:', r.version); console.log('  - Total workloads:', r.scan_summary.total_workloads); console.log('  - By status:', JSON.stringify(r.scan_summary.by_status)); console.log('  - By world:', JSON.stringify(r.scan_summary.by_world));"
echo ""
echo "🚀 Next steps:"
echo "  1. Start frontend: cd frontend && npm start"
echo "  2. Login as SuperAdmin"
echo "  3. Navigate to: http://localhost:3000/superadmin/workload-runtime"
echo ""
