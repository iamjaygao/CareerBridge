#!/bin/bash

##
## Sync Workload Frozen Bus Registry to Frontend
##
## Purpose: Copy the frozen bus registry from docs/ to frontend/public/
## so the frontend can read it as a static asset.
##

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${PROJECT_ROOT}/docs/WORKLOAD_FROZEN_BUS_REGISTRY.json"
TARGET_DIR="${PROJECT_ROOT}/frontend/public/registry"
TARGET="${TARGET_DIR}/WORKLOAD_FROZEN_BUS_REGISTRY.json"

echo "📦 Syncing Workload Frozen Bus Registry to frontend..."

# Ensure source exists
if [[ ! -f "$SOURCE" ]]; then
  echo "❌ Source registry not found: $SOURCE"
  echo "   Run: node scripts/build_frozen_registry.mjs first"
  exit 1
fi

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy registry
cp "$SOURCE" "$TARGET"

echo "✅ Registry synced!"
echo "   Source: $SOURCE"
echo "   Target: $TARGET"
echo ""
echo "🚀 Frontend can now access: /registry/WORKLOAD_FROZEN_BUS_REGISTRY.json"
