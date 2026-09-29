#!/usr/bin/env python3
"""
Summarise container memory from a docker-stats sample log.

Input lines (from the sampler): "<epoch>\t<name>\t<MemUsage like '123.4MiB / 15.6GiB'>"
Optional: a second file of "<name>\t<cgroup memory.peak bytes>".
Prints per-container sampled peak (and cgroup peak when available), plus totals.
"""
import sys
from collections import defaultdict

UNITS = {'B': 1 / 2**20, 'KiB': 1 / 1024, 'KB': 1 / 1024, 'MiB': 1, 'MB': 1, 'GiB': 1024, 'GB': 1024}


def to_mib(text):
    text = text.strip()
    for unit in sorted(UNITS, key=len, reverse=True):
        if text.endswith(unit):
            return float(text[:-len(unit)]) * UNITS[unit]
    return float(text) / 2**20


peak = defaultdict(float)
samples = defaultdict(int)
for line in open(sys.argv[1]):
    parts = line.rstrip('\n').split('\t')
    if len(parts) != 3 or '/' not in parts[2]:
        continue
    name, used = parts[1], to_mib(parts[2].split('/')[0])
    peak[name] = max(peak[name], used)
    samples[name] += 1

cgroup = {}
if len(sys.argv) > 2:
    for line in open(sys.argv[2]):
        name, _, value = line.strip().partition('\t')
        if value.isdigit():
            cgroup[name] = int(value) / 2**20

rows = sorted(peak, key=lambda n: -max(peak[n], cgroup.get(n, 0)))
out = ['| container | sampled peak (MiB) | cgroup memory.peak (MiB) | samples |', '|---|---|---|---|']
for n in rows:
    cg = f'{cgroup[n]:.1f}' if n in cgroup else 'n/a'
    out.append(f'| {n} | {peak[n]:.1f} | {cg} | {samples[n]} |')
total_sampled = sum(peak.values())
total_cgroup = sum(max(peak[n], cgroup.get(n, 0)) for n in peak)
out.append(f'| **sum of per-container peaks** | **{total_sampled:.1f}** | **{total_cgroup:.1f}** (max of both) | |')
print('\n'.join(out))
