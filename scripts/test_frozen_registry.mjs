#!/usr/bin/env node

/**
 * Minimal Test for Frozen Registry Scanner
 * 
 * Validates:
 * 1. Registry file exists
 * 2. Has correct structure (version, workloads)
 * 3. All workloads have required fields
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import assert from 'assert';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..');
const REGISTRY_PATH = path.join(PROJECT_ROOT, 'docs', 'WORKLOAD_FROZEN_REGISTRY.json');

console.log('🧪 Testing Frozen Registry...\n');

// Test 1: File exists
console.log('Test 1: Registry file exists');
assert(fs.existsSync(REGISTRY_PATH), 'Registry file not found');
console.log('✅ PASS\n');

// Test 2: Valid JSON
console.log('Test 2: Valid JSON structure');
const content = fs.readFileSync(REGISTRY_PATH, 'utf8');
let registry;
try {
  registry = JSON.parse(content);
} catch (err) {
  throw new Error('Invalid JSON: ' + err.message);
}
console.log('✅ PASS\n');

// Test 3: Has version
console.log('Test 3: Has version field');
assert(registry.version, 'Missing version field');
assert.strictEqual(typeof registry.version, 'string', 'Version must be string');
console.log(`✅ PASS (version: ${registry.version})\n`);

// Test 4: Has generated_at
console.log('Test 4: Has generated_at field');
assert(registry.generated_at, 'Missing generated_at field');
assert.strictEqual(typeof registry.generated_at, 'string', 'generated_at must be string');
console.log(`✅ PASS (generated: ${registry.generated_at})\n`);

// Test 5: Has scan_summary
console.log('Test 5: Has scan_summary');
assert(registry.scan_summary, 'Missing scan_summary');
assert(typeof registry.scan_summary.total_workloads === 'number', 'total_workloads must be number');
assert(registry.scan_summary.by_status, 'Missing by_status');
assert(registry.scan_summary.by_world, 'Missing by_world');
console.log(`✅ PASS (total: ${registry.scan_summary.total_workloads})\n`);

// Test 6: Has workloads array
console.log('Test 6: Has workloads array');
assert(Array.isArray(registry.workloads), 'workloads must be array');
assert(registry.workloads.length > 0, 'workloads array is empty');
console.log(`✅ PASS (${registry.workloads.length} workloads)\n`);

// Test 7: Workload structure
console.log('Test 7: Workload structure validation');
const requiredFields = ['name', 'kind', 'world', 'status', 'reason', 'entrypoints', 'signals'];
registry.workloads.forEach((wl, idx) => {
  requiredFields.forEach(field => {
    assert(wl[field] !== undefined, `Workload ${idx} missing field: ${field}`);
  });
  
  // Validate nested structures
  assert(Array.isArray(wl.entrypoints.frontend_routes), `Workload ${idx}: frontend_routes must be array`);
  assert(Array.isArray(wl.entrypoints.backend_prefixes), `Workload ${idx}: backend_prefixes must be array`);
  assert(Array.isArray(wl.signals.code_refs), `Workload ${idx}: code_refs must be array`);
  assert(Array.isArray(wl.signals.keywords), `Workload ${idx}: keywords must be array`);
});
console.log('✅ PASS\n');

// Test 8: Workloads sorted by name
console.log('Test 8: Workloads sorted alphabetically');
for (let i = 1; i < registry.workloads.length; i++) {
  const prev = registry.workloads[i - 1].name;
  const curr = registry.workloads[i].name;
  assert(prev.localeCompare(curr) <= 0, `Workloads not sorted: ${prev} > ${curr}`);
}
console.log('✅ PASS\n');

// Test 9: At least one workload has signals
console.log('Test 9: At least one workload has frozen signals');
const hasSignals = registry.workloads.some(wl => wl.signals.code_refs.length > 0);
assert(hasSignals, 'No workloads have frozen signals');
console.log('✅ PASS\n');

console.log('🎉 All tests passed!\n');
console.log('Summary:');
console.log(`  - Registry version: ${registry.version}`);
console.log(`  - Total workloads: ${registry.scan_summary.total_workloads}`);
console.log(`  - By status:`, registry.scan_summary.by_status);
console.log(`  - By world:`, registry.scan_summary.by_world);
