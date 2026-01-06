import zlib
from datetime import timezone as py_timezone
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from kernel.models import KernelAuditLog
from decision_slots.models import ResourceLock

def audit_stream(request):
    """
    API 1: KernelAudit Live Stream
    GET /kernel/observability/audit
    """
    # 1. Extract Query Params
    try:
        limit = int(request.GET.get("limit", 50))
    except ValueError:
        limit = 50
    limit = min(max(limit, 1), 200)

    since_id = request.GET.get("since_id")
    
    # 2. Query KernelAuditLog
    queryset = KernelAuditLog.objects.all()
    
    if since_id:
        try:
            queryset = queryset.filter(id__gt=int(since_id))
        except ValueError:
            pass
            
    # Order by id DESC (newest first)
    queryset = queryset.order_by("-id")[:limit]

    # 3. Format Response
    results = []
    for entry in queryset:
        # Field Source of Truth (MANDATORY)
        # 3a. Prioritize canonical fields with payload fallback
        resource_type = getattr(entry, "resource_type", None)
        resource_id = getattr(entry, "resource_id", None)
        outcome_code = getattr(entry, "outcome_code", None)
        
        payload = entry.payload or {}
        p_req = payload.get("request", {})
        p_abi = payload.get("abi", {})
        
        if resource_type is None:
            resource_type = p_req.get("resource_type")
        if resource_id is None:
            resource_id = p_req.get("resource_id")
        if outcome_code is None:
            outcome_code = p_abi.get("outcome_code")
            
        # 3b. Resource Hash (MANDATORY: from identity only)
        try:
            rid_val = int(resource_id)
        except (ValueError, TypeError):
            # Non-int or missing: stable stdlib hash
            rid_val = zlib.crc32(str(resource_id).encode()) & 0xffffffff
            
        resource_id_hash = f"#{rid_val % 1000:03d}"
        
        # 3c. Time Format (MANDATORY: UTC ISO-8601 with milliseconds)
        # Use astimezone(py_timezone.utc) to ensure UTC
        created_at_utc = entry.created_at.astimezone(py_timezone.utc)
        created_at_iso = created_at_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        
        results.append({
            "id": entry.id,
            "created_at": created_at_iso,
            "syscall_name": entry.event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_id_hash": resource_id_hash,
            "outcome_code": outcome_code,
            "trace_id": str(entry.event_id),
        })

    return JsonResponse(results, safe=False)


def lock_snapshot(request):
    """
    API 2: ResourceLock Snapshot
    GET /kernel/observability/locks
    """
    # 1. Extract Query Params
    active_only = request.GET.get("active_only", "true").lower() == "true"
    
    # 2. Query ResourceLock
    queryset = ResourceLock.objects.all()
    
    if active_only:
        now = timezone.now()
        queryset = queryset.filter(expires_at__gt=now, status="active")
        
    # Deterministic ordering
    queryset = queryset.order_by("resource_type", "resource_id")

    # 3. Format Response
    results = []
    for lock in queryset:
        results.append({
            "resource_type": lock.resource_type,
            "resource_id": lock.resource_id,
            "owner_id": lock.owner_id,
            "expires_at": lock.expires_at.isoformat() if lock.expires_at else None,
            "status": lock.status,
        })

    return JsonResponse(results, safe=False)


def kernel_pulse(request):
    """
    View: Kernel Pulse (Day-3 Sandbox)
    Serves the high-fidelity observability dashboard.
    Strictly READ-ONLY.
    """
    return render(request, 'kernel/pulse.html')
