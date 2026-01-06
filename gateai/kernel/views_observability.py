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



def compliance_monitor(request):
    """
    API 3: Compliance Monitor (Rapid Retry Detection)
    GET /kernel/observability/compliance
    """
    try:
        window_ms = int(request.GET.get("window_ms", 1500))
    except ValueError:
        window_ms = 1500
    window_ms = min(max(window_ms, 100), 10000)

    try:
        limit = int(request.GET.get("limit", 200))
    except ValueError:
        limit = 200
    limit = min(max(limit, 1), 500)

    # 1. Query last limit records
    queryset = KernelAuditLog.objects.all().order_by("-id")[:limit]
    
    # 2. Extract and sanitize records for comparison
    records = []
    for entry in queryset:
        payload = entry.payload or {}
        p_req = payload.get("request", {})
        p_abi = payload.get("abi", {})
        
        resource_type = getattr(entry, "resource_type", None) or p_req.get("resource_type")
        resource_id = getattr(entry, "resource_id", None) or p_req.get("resource_id")
        outcome_code = getattr(entry, "outcome_code", None) or p_abi.get("outcome_code")
        owner_id = p_req.get("owner_id")
        trace_id = str(entry.event_id)
        
        # New: context_hash for decision attribution
        context_hash = p_req.get("context_hash")
        
        # Resource Hash (re-use same logic as audit_stream)
        try:
            rid_val = int(resource_id)
        except (ValueError, TypeError):
            rid_val = zlib.crc32(str(resource_id).encode()) & 0xffffffff
        resource_id_hash = f"#{rid_val % 1000:03d}"

        records.append({
            "id": entry.id,
            "created_at": entry.created_at,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_id_hash": resource_id_hash,
            "outcome_code": outcome_code,
            "owner_id": owner_id,
            "trace_id": trace_id,
            "context_hash": context_hash,
        })

    # 3. Detect Violations
    violations = []
    # Both CONFLICT and FAILED_RETRYABLE require wait/backoff
    violation_outcome_codes = ["CONFLICT", "FAILED_RETRYABLE"]
    
    for i in range(len(records)):
        r1 = records[i]
        if r1["outcome_code"] not in violation_outcome_codes:
            continue
            
        for j in range(i + 1, len(records)):
            r2 = records[j]
            if r2["outcome_code"] not in violation_outcome_codes:
                continue
                
            # Identity Check
            # Match resource + owner (attribution)
            same_resource = (r1["resource_type"] == r2["resource_type"] and str(r1["resource_id"]) == str(r2["resource_id"]))
            same_owner = (r1["owner_id"] == r2["owner_id"] and r1["owner_id"] is not None)
            
            # Context Check (Decision identity)
            # If context_hash exists and is identical, it's definitely a retry of the same decision
            same_context = (r1["context_hash"] == r2["context_hash"] and r1["context_hash"] is not None)
            
            if same_resource and (same_owner or same_context):
                # Delta Check
                delta = abs((r1["created_at"] - r2["created_at"]).total_seconds() * 1000)
                
                # REQUISITE: Violation if same resource + same owner/context AND delta < 1500
                if delta <= window_ms:
                    # Attribution metadata
                    created_at_utc = r1["created_at"].astimezone(py_timezone.utc)
                    created_at_iso = created_at_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                    
                    violations.append({
                        "status": "VIOLATION",
                        "resource_type": r1["resource_type"],
                        "resource_id": r1["resource_id"],
                        "resource_id_hash": r1["resource_id_hash"],
                        "outcome_code": r1["outcome_code"],
                        "trace_id": r1["trace_id"],
                        "owner_id": r1["owner_id"],
                        "context_hash_tail": str(r1["context_hash"])[-8:] if r1["context_hash"] else None,
                        "created_at": created_at_iso,
                        "delta_ms": int(delta),
                        "reason": "Kernel Law Violation: Rapid retry (<1500ms) with same context/owner"
                    })
                    break # Skip to next record after detecting violation for r1

    return JsonResponse({
        "window_ms": window_ms,
        "checked": len(records),
        "violations": violations
    }, safe=False)


def kernel_pulse(request):
    """
    View: Kernel Pulse (Day-4 Constitution)
    Serves the high-fidelity observability dashboard.
    Strictly READ-ONLY.
    """
    return render(request, 'kernel/pulse.html')
