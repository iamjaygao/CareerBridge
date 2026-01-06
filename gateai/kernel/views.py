import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from kernel.syscalls import sys_claim
from kernel.abi import KernelOutcomeCode

@csrf_exempt
@require_POST
def dispatch_syscall(request):
    """
    Hardened HTTP entrypoint for GateAI Kernel syscalls.
    
    ROUTE: POST /kernel/dispatch
    """
    # 1. Trace ID Extraction
    trace_id = (
        request.headers.get("X-GateAI-TraceID") or
        request.headers.get("X-Trace-Id") or
        request.headers.get("X-Request-Id") or
        str(uuid.uuid4())
    )

    # 2. Body Validation
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return _error_response("Invalid JSON body", 400, trace_id)

    if not isinstance(data, dict):
        return _error_response("Body must be a JSON object", 400, trace_id)

    syscall_name = data.get("syscall_name")
    payload = data.get("payload")

    # 3. Request Validation
    if syscall_name != "sys_claim":
        return _error_response("Unsupported syscall", 400, trace_id)

    if not isinstance(payload, dict):
        return _error_response("Payload must be a JSON object", 400, trace_id)

    # 4. Inject Trace ID into payload (Reserved key)
    payload["_trace_id"] = trace_id

    # 5. Dispatch to Kernel
    # sys_claim is already Day-3 hardened and PRODUCTION-READY.
    result = sys_claim(payload)

    # 6. Map Outcome to HTTP Status
    status = _map_outcome_to_http_status(result.outcome)

    # 7. Response Format
    response_data = {
        "outcome_code": result.outcome_code,
        "kernel_error_code": result.outcome.get("error_code"),
        "message": result.outcome.get("public_message"),
        "trace_id": trace_id,
    }

    response = JsonResponse(response_data, status=status)
    response["X-GateAI-TraceID"] = trace_id
    return response


def _error_response(message, status, trace_id):
    response = JsonResponse({
        "message": message,
        "trace_id": trace_id
    }, status=status)
    response["X-GateAI-TraceID"] = trace_id
    return response


def _map_outcome_to_http_status(outcome):
    """
    ABI Mapping (Canonical names from kernel.abi):
    - outcome_code == OK or REPLAY        → HTTP 200
    - outcome_code == CONFLICT            → HTTP 409
    - outcome_code == REJECTED            → HTTP 400
    - outcome_code == FAILED_RETRYABLE    → HTTP 503
    - outcome_code == FAILED_FATAL        → HTTP 500
    
    If outcome.http_hint exists and is valid, it takes precedence.
    """
    hint = outcome.get("http_hint")
    if isinstance(hint, int):
        return hint

    code = outcome.get("outcome_code")
    
    mapping = {
        KernelOutcomeCode.OK: 200,
        KernelOutcomeCode.REPLAY: 200,
        KernelOutcomeCode.CONFLICT: 409,
        KernelOutcomeCode.REJECTED: 400,
        KernelOutcomeCode.FAILED_RETRYABLE: 503,
        KernelOutcomeCode.FAILED_FATAL: 500,
    }
    
    return mapping.get(code, 500)
