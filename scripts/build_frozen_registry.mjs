#!/usr/bin/env node

/**
 * Workload Frozen Registry Builder
 * 
 * Purpose: Automatically scan the CareerBridge/GateAI codebase to detect
 * frozen/disabled modules and generate a deterministic registry for the
 * Workload Runtime Console.
 * 
 * Phase-A.2: Avoid manual list drift - let code be the truth source.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..');

/**
 * Recursively find files matching extensions
 */
function findFiles(dir, extensions, ignore = []) {
  const results = [];
  
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(PROJECT_ROOT, fullPath);
      
      // Check ignore patterns
      if (ignore.some(pattern => relativePath.includes(pattern))) {
        continue;
      }
      
      if (entry.isDirectory()) {
        results.push(...findFiles(fullPath, extensions, ignore));
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (extensions.includes(ext)) {
          results.push(relativePath);
        }
      }
    }
  } catch (err) {
    // Ignore permission errors
  }
  
  return results;
}

// Frozen signal keywords to search for
const FROZEN_KEYWORDS = [
  'FROZEN',
  'frozen',
  'freeze',
  'disabled',
  'not_implemented',
  '404',
  'Phase-A freeze',
  'Frozen module',
  'LEGACY',
  'deprecated',
  'GHOST_WORLD',
];

// Input/Output files
const BUS_RULES_FILE = path.join(PROJECT_ROOT, 'docs', 'BUS_CLASSIFICATION_RULES.json');
const OUTPUT_FILE = path.join(PROJECT_ROOT, 'docs', 'WORKLOAD_FROZEN_BUS_REGISTRY.json');

console.log('🔍 Starting Workload Frozen Bus Registry scan...\n');

/**
 * Scan a file for frozen signals
 */
function scanFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    const signals = [];

    lines.forEach((line, idx) => {
      const trimmedLine = line.trim().toLowerCase();
      
      // Check for frozen keywords
      FROZEN_KEYWORDS.forEach(keyword => {
        if (trimmedLine.includes(keyword.toLowerCase())) {
          signals.push({
            keyword,
            line: idx + 1,
            snippet: line.trim().substring(0, 120),
          });
        }
      });
    });

    return signals;
  } catch (err) {
    console.warn(`⚠️  Could not read ${filePath}: ${err.message}`);
    return [];
  }
}

/**
 * Extract workload name from path
 */
function extractWorkloadName(filePath) {
  // Try to extract app/module name from path
  const match = filePath.match(/gateai\/([^\/]+)\//);
  if (match) return match[1];
  
  const frontendMatch = filePath.match(/frontend\/src\/pages\/([^\/]+)\//);
  if (frontendMatch) return frontendMatch[1];
  
  return null;
}

/**
 * Determine workload kind from path
 */
function determineKind(filePath) {
  if (filePath.includes('frontend/')) return 'frontend';
  if (filePath.includes('gateai/')) return 'backend';
  return 'fullstack';
}

/**
 * Determine world from path and content
 */
function determineWorld(filePath, signals) {
  if (filePath.includes('superadmin') || filePath.includes('kernel')) return 'kernel';
  if (filePath.includes('admin')) return 'admin';
  if (filePath.includes('student') || filePath.includes('mentor')) return 'app';
  
  // Check signals for world hints
  const worldHints = signals.flatMap(s => s.snippet.toLowerCase());
  if (worldHints.some(h => h.includes('kernel') || h.includes('superadmin'))) return 'kernel';
  if (worldHints.some(h => h.includes('admin'))) return 'admin';
  
  return 'app';
}

/**
 * Main scan function
 */
function scanRepository() {
  const workloadMap = new Map();
  
  const ignorePatterns = ['node_modules', '__pycache__', 'staticfiles', 'media', '.git', 'venv'];

  // Scan backend (gateai/)
  console.log('📂 Scanning backend (gateai/)...');
  const backendDir = path.join(PROJECT_ROOT, 'gateai');
  const backendFiles = findFiles(backendDir, ['.py', '.md'], ignorePatterns);

  for (const file of backendFiles) {
    const fullPath = path.join(PROJECT_ROOT, file);
    const signals = scanFile(fullPath);
    
    if (signals.length > 0) {
      const workloadName = extractWorkloadName(file);
      if (workloadName) {
        if (!workloadMap.has(workloadName)) {
          workloadMap.set(workloadName, {
            name: workloadName,
            kind: determineKind(file),
            world: determineWorld(file, signals),
            status: 'FROZEN',
            reason: 'Phase-A freeze (detected)',
            entrypoints: {
              frontend_routes: [],
              backend_prefixes: [],
            },
            signals: {
              code_refs: [],
              keywords: new Set(),
            },
          });
        }
        
        const workload = workloadMap.get(workloadName);
        signals.forEach(signal => {
          workload.signals.code_refs.push(`${file}:${signal.line}`);
          workload.signals.keywords.add(signal.keyword);
        });
      }
    }
  }

  // Scan frontend
  console.log('📂 Scanning frontend (frontend/src/)...');
  const frontendDir = path.join(PROJECT_ROOT, 'frontend', 'src');
  if (fs.existsSync(frontendDir)) {
    const frontendFiles = findFiles(frontendDir, ['.ts', '.tsx', '.md'], ignorePatterns);

    for (const file of frontendFiles) {
      const fullPath = path.join(PROJECT_ROOT, file);
      const signals = scanFile(fullPath);
      
      if (signals.length > 0) {
        const workloadName = extractWorkloadName(file) || 'frontend-misc';
        if (!workloadMap.has(workloadName)) {
          workloadMap.set(workloadName, {
            name: workloadName,
            kind: 'frontend',
            world: determineWorld(file, signals),
            status: 'FROZEN',
            reason: 'Phase-A freeze (detected)',
            entrypoints: {
              frontend_routes: [],
              backend_prefixes: [],
            },
            signals: {
              code_refs: [],
              keywords: new Set(),
            },
          });
        }
        
        const workload = workloadMap.get(workloadName);
        signals.forEach(signal => {
          workload.signals.code_refs.push(`${file}:${signal.line}`);
          workload.signals.keywords.add(signal.keyword);
        });
      }
    }
  }

  // Scan docs
  console.log('📂 Scanning docs (docs/)...');
  const docsDir = path.join(PROJECT_ROOT, 'docs');
  if (fs.existsSync(docsDir)) {
    const docsFiles = findFiles(docsDir, ['.md'], ignorePatterns);

    for (const file of docsFiles) {
      const fullPath = path.join(PROJECT_ROOT, file);
      const signals = scanFile(fullPath);
      
      if (signals.length > 0) {
        // Try to extract workload names from doc content
        const content = fs.readFileSync(fullPath, 'utf8');
        const workloadMatches = content.match(/\b(search|dashboard|analytics|jobs|resumes|appointments|mentors)\b/gi);
        
        if (workloadMatches) {
          const uniqueWorkloads = [...new Set(workloadMatches.map(w => w.toLowerCase()))];
          uniqueWorkloads.forEach(workloadName => {
            if (!workloadMap.has(workloadName)) {
              workloadMap.set(workloadName, {
                name: workloadName,
                kind: 'fullstack',
                world: 'app',
                status: 'UNKNOWN_FROZEN_SIGNAL',
                reason: 'Detected in documentation',
                entrypoints: {
                  frontend_routes: [],
                  backend_prefixes: [],
                },
                signals: {
                  code_refs: [],
                  keywords: new Set(),
                },
              });
            }
            
            const workload = workloadMap.get(workloadName);
            signals.forEach(signal => {
              workload.signals.code_refs.push(`${file}:${signal.line}`);
              workload.signals.keywords.add(signal.keyword);
            });
          });
        }
      }
    }
  }

  // Add known workloads (status will be determined by bus power)
  const knownWorkloads = [
    {
      name: 'legacy-admin-dashboard',
      kind: 'frontend',
      world: 'admin',
      status: 'FROZEN',
      reason: 'Phase-A: Isolated from SuperAdmin kernel world',
      entrypoints: {
        frontend_routes: ['/admin/legacy-dashboard'],
        backend_prefixes: [],
      },
    },
    {
      name: 'peer-mock-runtime',
      kind: 'fullstack',
      world: 'kernel',
      status: 'FROZEN',
      reason: 'Experimental capability - Phase-A',
      entrypoints: {
        frontend_routes: ['/superadmin/runtime/peer'],
        backend_prefixes: ['/api/v1/peer/', '/api/v1/mock/'],
      },
    },
  ];

  knownWorkloads.forEach(wl => {
    if (!workloadMap.has(wl.name)) {
      workloadMap.set(wl.name, {
        ...wl,
        signals: {
          code_refs: ['(known workload)'],
          keywords: new Set(['workload']),
        },
      });
    }
  });

  return Array.from(workloadMap.values());
}

/**
 * Load bus classification rules
 */
function loadBusRules() {
  try {
    const content = fs.readFileSync(BUS_RULES_FILE, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    console.error('❌ Failed to load bus classification rules:', err.message);
    console.error('   Creating default rules...');
    return {
      version: '0.1',
      rules: [],
      fallback_bus: 'UNKNOWN_BUS'
    };
  }
}

/**
 * Load bus power states from bus_power.py (source of truth)
 */
function loadBusPowerStates() {
  try {
    const busPowerFile = path.join(PROJECT_ROOT, 'gateai', 'kernel', 'policies', 'bus_power.py');
    const content = fs.readFileSync(busPowerFile, 'utf8');
    
    // Parse BUS_POWER dict from Python file
    const busStates = {};
    const busPowerMatch = content.match(/BUS_POWER\s*=\s*\{([^}]+)\}/s);
    
    if (busPowerMatch) {
      const dictContent = busPowerMatch[1];
      const lines = dictContent.split('\n');
      
      for (const line of lines) {
        const match = line.match(/"([^"]+)":\s*"(ON|OFF)"/);
        if (match) {
          busStates[match[1]] = match[2];
        }
      }
    }
    
    console.log('📋 Loaded bus power states from bus_power.py:', busStates);
    return busStates;
  } catch (err) {
    console.error('⚠️  Failed to load bus power states:', err.message);
    console.error('   Using default: KERNEL_CORE_BUS=ON, all others=OFF');
    return {
      'KERNEL_CORE_BUS': 'ON',
      'PEER_MOCK_BUS': 'OFF',
    };
  }
}

/**
 * Classify workload to bus based on GateAI Capability Constitution
 * 
 * Canonical 8 Buses:
 * 1. KERNEL_CORE_BUS (kernel, superadmin)
 * 2. PUBLIC_WEB_BUS (landing, marketing, public)
 * 3. ADMIN_BUS (staff, audit, ops, console, admin)
 * 4. AI_BUS (ai, ats, signals, engine, decision_slots, chat)
 * 5. PEER_MOCK_BUS (peer, mock, simulator, runtime_mock)
 * 6. MENTOR_BUS (mentor, appointments, human_loop, availability)
 * 7. PAYMENT_BUS (payments, stripe, billing)
 * 8. SEARCH_BUS (search, analytics)
 */
function classifyWorkloadToBus(workload, busRules) {
  const name = workload.name.toLowerCase();
  const world = workload.world.toLowerCase();
  const signals = workload.signals.keywords.map(k => k.toLowerCase()).join(' ');
  const refs = workload.signals.code_refs.join(' ').toLowerCase();
  const routes = [
    ...workload.entrypoints.frontend_routes,
    ...workload.entrypoints.backend_prefixes
  ].map(r => r.toLowerCase()).join(' ');
  
  const allText = `${name} ${world} ${signals} ${refs} ${routes}`;
  
  // 1. KERNEL_CORE_BUS (highest priority)
  if (world === 'kernel' || 
      name === 'kernel' || 
      allText.includes('superadmin') ||
      allText.includes('/kernel/')) {
    return 'KERNEL_CORE_BUS';
  }
  
  // 2. PEER_MOCK_BUS (simulation, testing, mocking)
  if (name.includes('peer') || 
      name.includes('mock') || 
      name.includes('simulator') ||
      allText.includes('peer-mock') ||
      allText.includes('runtime-mock') ||
      allText.includes('peer_mock')) {
    return 'PEER_MOCK_BUS';
  }
  
  // 3. AI_BUS (consolidated: ai, ats, signals, engines, decision_slots, chat)
  if (name.includes('ai') ||
      name.includes('ats') ||
      name.includes('signal') ||
      name.includes('engine') ||
      name.includes('decision') ||
      name.includes('chat') ||
      allText.includes('ats_signals') ||
      allText.includes('signal_delivery')) {
    return 'AI_BUS';
  }
  
  // 4. MENTOR_BUS (appointments, human_loop, availability)
  if (name.includes('mentor') ||
      name.includes('appointment') ||
      name.includes('human_loop') ||
      name.includes('availability')) {
    return 'MENTOR_BUS';
  }
  
  // 5. PAYMENT_BUS (payments, stripe, billing)
  if (name.includes('payment') ||
      name.includes('stripe') ||
      name.includes('billing')) {
    return 'PAYMENT_BUS';
  }
  
  // 6. SEARCH_BUS (search, analytics)
  if (name.includes('search') ||
      name.includes('analytics')) {
    return 'SEARCH_BUS';
  }
  
  // 7. ADMIN_BUS (consolidated: staff, admin, audit, ops, console)
  if (world === 'admin' ||
      name.includes('admin') ||
      name.includes('staff') ||
      name.includes('audit') ||
      name.includes('ops') ||
      name.includes('console') ||
      allText.includes('/admin/') ||
      allText.includes('/staff/')) {
    return 'ADMIN_BUS';
  }
  
  // 8. PUBLIC_WEB_BUS (fallback for app world and public content)
  if (world === 'app' || world === 'public') {
    return 'PUBLIC_WEB_BUS';
  }
  
  // Unknown workloads
  return 'PUBLIC_WEB_BUS';  // Default fallback
}

/**
 * Build final registry (Bus-aggregated)
 */
function buildRegistry() {
  const workloads = scanRepository();

  // Load bus classification rules
  const busRules = loadBusRules();
  console.log(`📋 Loaded ${busRules.rules.length} bus classification rules\n`);
  
  // Convert Sets to Arrays for JSON serialization
  const serializedWorkloads = workloads.map(wl => ({
    ...wl,
    signals: {
      code_refs: wl.signals.code_refs.slice(0, 10), // Limit to top 10 refs
      keywords: Array.from(wl.signals.keywords),
    },
  }));

  // Classify each workload to a bus
  console.log('🏷️  Classifying workloads to buses...\n');
  
  // Initialize all canonical 8 buses (GateAI Capability Constitution)
  const CANONICAL_BUSES = [
    'KERNEL_CORE_BUS',
    'PUBLIC_WEB_BUS',
    'ADMIN_BUS',
    'AI_BUS',
    'PEER_MOCK_BUS',
    'MENTOR_BUS',
    'PAYMENT_BUS',
    'SEARCH_BUS',
  ];
  
  // Load bus power state from source of truth (bus_power.py)
  const busPowerStates = loadBusPowerStates();
  
  const busMap = new Map();
  CANONICAL_BUSES.forEach(busId => {
    busMap.set(busId, {
      state: busPowerStates[busId] || 'OFF',
      workloads: [],
    });
  });
  
  // Classify and assign workloads to buses
  serializedWorkloads.forEach(wl => {
    const bus = classifyWorkloadToBus(wl, busRules);
    
    // Update workload status based on bus power state
    const busState = busMap.has(bus) ? busMap.get(bus).state : 'OFF';
    if (busState === 'ON') {
      wl.status = 'ACTIVE';
      wl.reason = 'Bus is powered ON';
    }
    
    // If classified bus is not canonical, assign to PUBLIC_WEB_BUS
    if (!busMap.has(bus)) {
      console.log(`⚠️  Non-canonical bus "${bus}" detected for workload "${wl.name}", assigning to PUBLIC_WEB_BUS`);
      busMap.get('PUBLIC_WEB_BUS').workloads.push(wl);
    } else {
      busMap.get(bus).workloads.push(wl);
    }
  });
  
  // Sort workloads within each bus
  busMap.forEach(busData => {
    busData.workloads.sort((a, b) => a.name.localeCompare(b.name));
  });
  
  // Convert Map to sorted object
  const buses = {};
  const sortedBusNames = Array.from(busMap.keys()).sort();
  sortedBusNames.forEach(busName => {
    buses[busName] = busMap.get(busName);
  });
  
  // Calculate summary statistics
  const totalWorkloads = serializedWorkloads.length;
  const byBus = {};
  sortedBusNames.forEach(busName => {
    byBus[busName] = busMap.get(busName).workloads.length;
  });

  const registry = {
    version: '0.2',
    generated_at: new Date().toISOString(),
    scan_summary: {
      total_workloads: totalWorkloads,
      total_buses: sortedBusNames.length,
      by_bus: byBus,
    },
    buses: buses,
  };

  return registry;
}

/**
 * Main execution
 */
function main() {
  try {
    const registry = buildRegistry();

    // Ensure output directory exists
    const outputDir = path.dirname(OUTPUT_FILE);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Write to file
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(registry, null, 2), 'utf8');

    console.log('\n✅ Registry generated successfully!\n');
    console.log(`📄 Output: ${OUTPUT_FILE}`);
    console.log(`📊 Total workloads: ${registry.scan_summary.total_workloads}`);
    console.log(`🚌 Total buses: ${registry.scan_summary.total_buses}`);
    console.log(`📈 By bus:`, registry.scan_summary.by_bus);
    console.log('\n✨ Run sync script to copy to frontend:\n   ./scripts/sync_registry_to_frontend.sh\n');
  } catch (err) {
    console.error('❌ Error building registry:', err);
    process.exit(1);
  }
}

main();
