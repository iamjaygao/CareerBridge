#!/usr/bin/env python3
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KERNEL PHYSICAL ARBITER: ResourceLock De-duplication Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
Prepare database for UNIQUE(resource_type, resource_id) constraint.

GUARANTEES:
- Deterministic arbitration
- Auditable deletions
- Atomic execution
- Production-safe
- Idempotent

REQUIREMENTS:
- PRE_MIGRATION_SNAPSHOT_TAKEN=YES must be set
- Django environment configured

USAGE:
    python scripts/dedupe_resource_locks.py --dry-run
    python scripts/dedupe_resource_locks.py --dry-run --verbose
    python scripts/dedupe_resource_locks.py --execute
    python scripts/dedupe_resource_locks.py --execute --verbose

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import argparse
import django
from typing import Dict, List, Tuple

# Django setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')
django.setup()

from django.db import transaction
from django.db.models import Count
from decision_slots.models import ResourceLock


class ResourceLockArbiter:
    """
    Production-safe de-duplication arbiter for ResourceLock records.
    
    Implements deterministic tie-breaking and atomic deletion.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize arbiter.
        
        Args:
            verbose: Enable detailed audit logging
        """
        self.verbose = verbose
        self.duplicate_groups_found = 0
        self.total_rows_to_delete = 0
        self.deletion_plan: List[Dict] = []
    
    def check_environment_gate(self) -> bool:
        """
        Verify pre-migration snapshot acknowledgment.
        
        Returns:
            True if gate passed, False otherwise
        """
        snapshot_ack = os.environ.get('PRE_MIGRATION_SNAPSHOT_TAKEN', '').upper()
        
        if snapshot_ack != 'YES':
            print("━" * 70)
            print("❌ ENVIRONMENT GATE FAILED")
            print("━" * 70)
            print()
            print("Pre-migration snapshot required.")
            print("This arbiter will NOT run without explicit acknowledgment.")
            print()
            print("Please run:")
            print("    export PRE_MIGRATION_SNAPSHOT_TAKEN=YES")
            print()
            print("Then re-run this script.")
            print("━" * 70)
            return False
        
        return True
    
    def find_duplicate_groups(self) -> List[Tuple[str, int, int]]:
        """
        Find all duplicate (resource_type, resource_id) groups.
        
        Uses DB-level aggregation for memory efficiency.
        
        Returns:
            List of (resource_type, resource_id, count) tuples
        """
        duplicates = (
            ResourceLock.objects
            .values('resource_type', 'resource_id')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('resource_type', 'resource_id')
        )
        
        return [
            (dup['resource_type'], dup['resource_id'], dup['count'])
            for dup in duplicates
        ]
    
    def compute_deletion_plan(
        self, 
        duplicate_groups: List[Tuple[str, int, int]]
    ) -> None:
        """
        Compute deterministic deletion plan for all duplicate groups.
        
        For each group:
        1. ORDER BY expires_at DESC, id DESC
        2. KEEP the first record (highest expires_at, highest id)
        3. DELETE all others
        
        Args:
            duplicate_groups: List of (resource_type, resource_id, count) tuples
        """
        self.duplicate_groups_found = len(duplicate_groups)
        self.deletion_plan = []
        
        for resource_type, resource_id, count in duplicate_groups:
            # Fetch all locks for this (resource_type, resource_id)
            # Order by expires_at DESC, id DESC
            locks = list(
                ResourceLock.objects
                .filter(resource_type=resource_type, resource_id=resource_id)
                .order_by('-expires_at', '-id')
                .values('id', 'decision_id', 'expires_at', 'status', 'owner_id')
            )
            
            if not locks:
                continue  # Should never happen, but safety first
            
            # KEEP first record (deterministic winner)
            winner = locks[0]
            
            # DELETE all others
            losers = locks[1:]
            
            for loser in losers:
                self.deletion_plan.append({
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'lock_id': loser['id'],
                    'decision_id': loser['decision_id'],
                    'expires_at': loser['expires_at'],
                    'status': loser['status'],
                    'owner_id': loser['owner_id'],
                    'winner_id': winner['id'],
                    'winner_expires_at': winner['expires_at'],
                })
        
        self.total_rows_to_delete = len(self.deletion_plan)
    
    def print_deletion_plan(self) -> None:
        """
        Print deletion plan to stdout.
        
        Shows summary and detailed audit log if verbose enabled.
        """
        print()
        print("━" * 70)
        print("DELETION PLAN SUMMARY")
        print("━" * 70)
        print(f"Duplicate groups found: {self.duplicate_groups_found}")
        print(f"Total rows to delete: {self.total_rows_to_delete}")
        print("━" * 70)
        
        if self.verbose and self.deletion_plan:
            print()
            print("━" * 70)
            print("DETAILED DELETION AUDIT")
            print("━" * 70)
            
            # Group by (resource_type, resource_id) for readability
            current_group = None
            
            for item in self.deletion_plan:
                group_key = (item['resource_type'], item['resource_id'])
                
                if current_group != group_key:
                    current_group = group_key
                    print()
                    print(f"GROUP: {item['resource_type']} :: {item['resource_id']}")
                    print(f"  WINNER: Lock ID {item['winner_id']} "
                          f"(expires_at={item['winner_expires_at']})")
                    print(f"  DELETIONS:")
                
                print(f"    ├─ Lock ID {item['lock_id']}")
                print(f"    │  ├─ decision_id: {item['decision_id']}")
                print(f"    │  ├─ expires_at: {item['expires_at']}")
                print(f"    │  ├─ status: {item['status']}")
                print(f"    │  └─ owner_id: {item['owner_id']}")
            
            print()
            print("━" * 70)
    
    def execute_deletions(self) -> int:
        """
        Execute physical deletions atomically.
        
        All deletions occur within a single transaction.
        If ANY deletion fails, ALL are rolled back.
        
        Returns:
            Number of rows deleted
        """
        if not self.deletion_plan:
            return 0
        
        with transaction.atomic():
            # Extract all lock IDs to delete
            lock_ids_to_delete = [item['lock_id'] for item in self.deletion_plan]
            
            # Atomic bulk delete
            deleted_count, _ = (
                ResourceLock.objects
                .filter(id__in=lock_ids_to_delete)
                .delete()
            )
            
            return deleted_count
    
    def run_dry_run(self) -> None:
        """
        Execute dry-run mode (no deletions).
        """
        print("━" * 70)
        print("MODE: DRY RUN")
        print("━" * 70)
        print("No deletions will be performed.")
        print("This is a simulation only.")
        print("━" * 70)
        
        # Find duplicates
        duplicate_groups = self.find_duplicate_groups()
        
        if not duplicate_groups:
            print()
            print("✅ No duplicates found.")
            print("Database is ready for UNIQUE constraint.")
            print()
            return
        
        # Compute deletion plan
        self.compute_deletion_plan(duplicate_groups)
        
        # Print plan
        self.print_deletion_plan()
        
        print()
        print("━" * 70)
        print("DRY RUN COMPLETE")
        print("━" * 70)
        print("To execute deletions, run with --execute flag:")
        print("    python scripts/dedupe_resource_locks.py --execute")
        print("━" * 70)
    
    def run_execute(self) -> None:
        """
        Execute deletion mode (physical deletions).
        """
        print("━" * 70)
        print("MODE: EXECUTE")
        print("━" * 70)
        print("⚠️  PHYSICAL DELETIONS WILL BE PERFORMED")
        print("━" * 70)
        
        # Find duplicates
        duplicate_groups = self.find_duplicate_groups()
        
        if not duplicate_groups:
            print()
            print("✅ No duplicates found.")
            print("Database is ready for UNIQUE constraint.")
            print()
            return
        
        # Compute deletion plan
        self.compute_deletion_plan(duplicate_groups)
        
        # Print plan
        self.print_deletion_plan()
        
        # Execute deletions
        print()
        print("━" * 70)
        print("EXECUTING DELETIONS...")
        print("━" * 70)
        
        try:
            deleted_count = self.execute_deletions()
            
            print()
            print("━" * 70)
            print("✅ EXECUTION COMPLETE")
            print("━" * 70)
            print(f"Rows deleted: {deleted_count}")
            print("Database is now ready for UNIQUE constraint.")
            print("━" * 70)
            
        except Exception as e:
            print()
            print("━" * 70)
            print("❌ EXECUTION FAILED")
            print("━" * 70)
            print(f"Error: {e}")
            print()
            print("Transaction has been rolled back.")
            print("No changes were made to the database.")
            print("━" * 70)
            raise


def main():
    """
    Main entry point for arbiter script.
    """
    parser = argparse.ArgumentParser(
        description='ResourceLock de-duplication arbiter (Kernel Physical Arbiter)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default) - shows deletion plan without executing
  python scripts/dedupe_resource_locks.py --dry-run
  
  # Dry run with verbose audit log
  python scripts/dedupe_resource_locks.py --dry-run --verbose
  
  # Execute deletions (requires snapshot acknowledgment)
  export PRE_MIGRATION_SNAPSHOT_TAKEN=YES
  python scripts/dedupe_resource_locks.py --execute
  
  # Execute with verbose audit log
  python scripts/dedupe_resource_locks.py --execute --verbose

Safety:
  - Requires PRE_MIGRATION_SNAPSHOT_TAKEN=YES environment variable
  - Atomic execution (all-or-nothing)
  - Deterministic arbitration
  - Idempotent (safe to re-run)
        """
    )
    
    # Execution mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show deletion plan without executing (DEFAULT)'
    )
    mode_group.add_argument(
        '--execute',
        action='store_true',
        help='Execute physical deletions'
    )
    
    # Verbosity
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed audit log for every deletion'
    )
    
    args = parser.parse_args()
    
    # Handle mutually exclusive group default
    if not args.execute:
        args.dry_run = True
    
    # Initialize arbiter
    arbiter = ResourceLockArbiter(verbose=args.verbose)
    
    # Environment gate check
    if not arbiter.check_environment_gate():
        sys.exit(1)
    
    # Execute appropriate mode
    try:
        if args.execute:
            arbiter.run_execute()
        else:
            arbiter.run_dry_run()
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print()
        print("━" * 70)
        print("⚠️  INTERRUPTED BY USER")
        print("━" * 70)
        sys.exit(130)
        
    except Exception as e:
        print()
        print("━" * 70)
        print("❌ FATAL ERROR")
        print("━" * 70)
        print(f"Error: {e}")
        print("━" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

