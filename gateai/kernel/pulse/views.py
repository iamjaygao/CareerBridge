"""
Kernel Pulse Views - Phase-A.1

Read-only kernel observability endpoint.
Protected by Kernel GovernanceMiddleware (superuser + kernel world only).
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from kernel.models import KernelAuditLog
from decision_slots.models import ResourceLock


class KernelPulseSummaryView(APIView):
    """
    GET /kernel/pulse/summary/
    
    Returns kernel state reconstruction from audit logs.
    
    Pulse ABI v0.1 (Frozen Contract):
    - pulse_version: "0.1"
    - now: ISO8601 timestamp
    - kernel_state: {mode, active_lock_pressure, error_rate_1h, chaos_safe}
    - recent_syscalls: Last 20 syscalls
    - counts: {last_1h, last_24h} aggregates
    - active_locks: Current active locks
    - top_errors_24h: Most common errors
    
    Security:
    - Protected by GovernanceMiddleware (kernel world check)
    - Additional DRF permission (IsAuthenticated)
    - Superuser-only via middleware
    """
    
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        now = timezone.now()
        
        # Time windows
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        # Recent syscalls (last 20)
        recent_syscalls = KernelAuditLog.objects.order_by('-created_at')[:20]
        recent_syscalls_data = [
            {
                "at": log.created_at.isoformat(),
                "syscall": log.event_type or "unknown",
                "decision_slot_id": log.decision_id or None,
                "outcome": log.status or "EMITTED",
                "error_code": log.failure_reason if log.failure_reason else None,
                "trace_id": str(log.event_id),
                "resource_type": None,  # Not in current model
                "resource_id": None,    # Not in current model
                "owner_id": None,       # Not in current model
            }
            for log in recent_syscalls
        ]
        
        # Counts - Last 1h
        logs_1h = KernelAuditLog.objects.filter(created_at__gte=one_hour_ago)
        counts_1h = self._compute_counts(logs_1h)
        
        # Counts - Last 24h
        logs_24h = KernelAuditLog.objects.filter(created_at__gte=twenty_four_hours_ago)
        counts_24h = self._compute_counts(logs_24h)
        
        # Error rate (1h)
        error_rate_1h = 0.0
        if counts_1h['total'] > 0:
            error_rate_1h = (counts_1h['terminal'] + counts_1h['conflict']) / counts_1h['total']
        
        # Active locks
        active_locks_qs = ResourceLock.objects.filter(
            Q(status='LOCKED') | Q(status='HELD')
        )
        # If expires_at exists, filter by not expired
        active_locks_qs = active_locks_qs.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        active_locks_count = active_locks_qs.count()
        active_locks_samples = [
            {
                "resource_type": lock.resource_type,
                "resource_id": lock.resource_id,
                "owner_id": str(lock.owner_id) if lock.owner_id else None,
                "expires_at": lock.expires_at.isoformat() if lock.expires_at else None,
                "status": lock.status,
            }
            for lock in active_locks_qs[:10]  # Sample first 10
        ]
        
        # Top errors (24h)
        top_errors = (
            KernelAuditLog.objects
            .filter(created_at__gte=twenty_four_hours_ago)
            .exclude(failure_reason='')
            .exclude(failure_reason__isnull=True)
            .values('failure_reason')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        top_errors_data = [
            {"error_code": e['failure_reason'][:100], "count": e['count']}  # Truncate long errors
            for e in top_errors
        ]
        
        # Kernel state derivation
        if error_rate_1h >= 0.2:
            mode = "LOCKED"
        elif error_rate_1h >= 0.05:
            mode = "DEGRADED"
        else:
            mode = "NORMAL"
        
        if active_locks_count >= 100:
            lock_pressure = "HIGH"
        elif active_locks_count >= 10:
            lock_pressure = "MEDIUM"
        else:
            lock_pressure = "LOW"
        
        chaos_safe = (mode != "LOCKED")
        
        # Pulse ABI v0.1
        return Response({
            "pulse_version": "0.1",
            "now": now.isoformat(),
            "kernel_state": {
                "mode": mode,
                "active_lock_pressure": lock_pressure,
                "error_rate_1h": round(error_rate_1h, 4),
                "chaos_safe": chaos_safe,
            },
            "recent_syscalls": recent_syscalls_data,
            "counts": {
                "last_1h": counts_1h,
                "last_24h": counts_24h,
            },
            "active_locks": {
                "count": active_locks_count,
                "samples": active_locks_samples,
            },
            "top_errors_24h": top_errors_data,
        })
    
    def _compute_counts(self, queryset):
        """Compute success/failure counts from queryset"""
        total = queryset.count()
        
        # Count by status (KernelAuditLog uses: EMITTED, HANDLED, FAILED, REJECTED)
        success = queryset.filter(status='HANDLED').count()
        retryable = queryset.filter(status='EMITTED').count()  # In progress/pending
        terminal = queryset.filter(status='FAILED').count()
        conflict = queryset.filter(status='REJECTED').count()
        
        return {
            "total": total,
            "success": success,
            "retryable": retryable,
            "terminal": terminal,
            "conflict": conflict,
        }
