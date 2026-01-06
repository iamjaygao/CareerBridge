import uuid
import logging
from django.conf import settings
from django.http import JsonResponse, Http404
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from kernel.syscalls import sys_claim
from kernel.abi import KernelOutcomeCode
from decision_slots.models import ResourceLock

logger = logging.getLogger(__name__)

@csrf_exempt
def atomic_trap(request):
    """
    Sandbox-only endpoint to trigger the atomic block guard in sys_claim.
    Goal: Prove that syscalls fail with FAILED_RETRYABLE if called inside outer atomic.
    """
    if not settings.DEBUG:
        raise Http404("Sandbox only")

    # 1. Pre-seed a lock OUTSIDE the outer atomic to ensure conflict
    resource_type = "demo"
    resource_id = 999
    
    # We use update_or_create for stability
    ResourceLock.objects.update_or_create(
        resource_type=resource_type,
        resource_id=resource_id,
        defaults={
            "owner_id": 888, # seed-owner ID
            "expires_at": timezone.now() + timezone.timedelta(hours=1),
            "status": "active",
            "decision_id": "trap-seed"
        }
    )

    # Trace ID extraction (from header or generate)
    trace_id = request.headers.get("X-GateAI-TraceID") or f"chaos-C-{uuid.uuid4().hex[:4]}"
    
    payload = {
        "decision_id": f"dec-trap-{uuid.uuid4().hex[:8]}",
        "context_hash": f"ctx-trap-{uuid.uuid4().hex[:8]}",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "owner_id": 999, # trap-owner ID
        "expires_at": (timezone.now() + timezone.timedelta(hours=1)).isoformat(),
        "_trace_id": trace_id
    }

    # 2. Enter outer transaction.atomic()
    # This forces get_connection().in_atomic_block to be True during sys_claim's post-atomic check.
    try:
        with transaction.atomic():
            # sys_claim will:
            # - Allocate audit
            # - Try to create lock
            # - Fail with IntegrityError (physically locked by seed-owner)
            # - Detect that it is STILL inside an atomic block
            # - Return FAILED_RETRYABLE (503)
            result = sys_claim(payload)
            outcome_code = result.outcome_code
            message = result.outcome.get("public_message") or result.outcome.get("message")
            kernel_error_code = result.outcome.get("error_code")
    except Exception as e:
        logger.error(f"Atomic trap wrapper unexpected error: {e}")
        outcome_code = KernelOutcomeCode.FAILED_FATAL
        message = str(e)
        kernel_error_code = "SANDBOX_TRAP_FAILURE"

    # Canonical ABI mapping
    status_map = {
        KernelOutcomeCode.OK: 200,
        KernelOutcomeCode.REPLAY: 200,
        KernelOutcomeCode.CONFLICT: 409,
        KernelOutcomeCode.REJECTED: 400,
        KernelOutcomeCode.FAILED_RETRYABLE: 503,
        KernelOutcomeCode.FAILED_FATAL: 500,
    }
    
    status_code = status_map.get(outcome_code, 500)
    
    response_data = {
        "outcome_code": outcome_code,
        "kernel_error_code": kernel_error_code,
        "message": message,
        "trace_id": trace_id,
    }
    
    response = JsonResponse(response_data, status=status_code)
    response["X-GateAI-TraceID"] = trace_id
    return response
