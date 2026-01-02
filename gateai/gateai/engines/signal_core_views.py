"""
Signal Core Engine API Views.

Production-safe API endpoints for engine execution.
Exposes ResumeAuditEngine via reserved namespace: /api/engines/signal-core/
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from pydantic import ValidationError

from gateai.engines.resume_audit import ResumeAuditEngine
from gateai.engines.resume_audit.schemas import ResumeAuditInput
from ats_signals.services.persistence import persist_engine_signals
from signal_delivery.services.dispatcher import on_signal_created

logger = logging.getLogger(__name__)

# GateAI OS Contract version
CONTRACT_VERSION = "1.0.1"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resume_audit_view(request):
    """
    Resume Audit Engine endpoint.
    
    POST /api/engines/signal-core/resume-audit/
    
    Accepts JSON input, dispatches ResumeAuditEngine, returns structured output.
    
    Request Body:
    {
        "decision_slot_id": "ds_12345",  # Required
        "resume_id": "resume_123",      # Required
        "resume_text": "...",           # Required
        "user_id": "user_456",          # Required
        "target_job_title": "...",       # Optional
        "target_industry": "...",        # Optional
        "target_keywords": [...],        # Optional
        "analysis_depth": "standard",    # Optional: basic|standard|comprehensive
        "include_recommendations": true, # Optional
        "include_ats_compatibility": true # Optional
    }
    
    Response:
    {
        "engine": "ResumeAuditEngine",
        "contract_version": "1.0.1",
        "engine_output": {...},
        "trace": {
            "latency_ms": 150,
            "tokens_used": null,
            "model_version": null
        }
    }
    
    Rules:
    - No DB writes inside engine (engine is stateless)
    - Endpoint does not alter kernel data
    - Errors trigger fallback logic
    - Always returns valid output
    """
    try:
        # Extract decision_slot_id (required)
        decision_slot_id = request.data.get('decision_slot_id')
        if not decision_slot_id:
            return Response(
                {
                    'error': 'Missing required field',
                    'message': 'decision_slot_id is required',
                    'field': 'decision_slot_id'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate decision_slot_id format
        if not isinstance(decision_slot_id, str) or len(decision_slot_id.strip()) == 0:
            return Response(
                {
                    'error': 'Invalid decision_slot_id',
                    'message': 'decision_slot_id must be a non-empty string',
                    'field': 'decision_slot_id'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare engine input (exclude decision_slot_id from input dict)
        engine_input = {k: v for k, v in request.data.items() if k != 'decision_slot_id'}
        
        # Initialize engine
        engine = ResumeAuditEngine()
        
        # Validate input against schema
        try:
            validated_input = engine.input_schema(**engine_input)
        except ValidationError as e:
            return Response(
                {
                    'error': 'Input validation failed',
                    'message': 'Input does not conform to ResumeAuditInput schema',
                    'details': e.errors()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Dispatch engine with error handling
        try:
            engine_output = engine.run(engine_input, decision_slot_id)
        except Exception as e:
            # Log error
            logger.error(
                f"ResumeAuditEngine execution failed: {str(e)}",
                exc_info=True,
                extra={
                    'decision_slot_id': decision_slot_id,
                    'user_id': request.user.id,
                    'resume_id': engine_input.get('resume_id'),
                }
            )
            
            # Use fallback logic (Rule 7: Resilience)
            try:
                engine_output = engine.fallback_logic(e, engine_input, decision_slot_id)
            except Exception as fallback_error:
                # If fallback also fails, return minimal error response
                logger.critical(
                    f"ResumeAuditEngine fallback_logic failed: {str(fallback_error)}",
                    exc_info=True
                )
                return Response(
                    {
                        'error': 'Engine execution failed',
                        'message': 'Engine and fallback logic both failed',
                        'engine': 'ResumeAuditEngine',
                        'contract_version': CONTRACT_VERSION,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Validate output schema (Rule 14: AUTOMATED CONTRACT TESTING)
        try:
            engine.output_schema(**engine_output)
        except ValidationError as e:
            logger.error(
                f"ResumeAuditEngine output validation failed: {str(e)}",
                exc_info=True,
                extra={
                    'decision_slot_id': decision_slot_id,
                    'user_id': request.user.id,
                }
            )
            # Use fallback if output validation fails
            try:
                fallback_error = Exception("Output schema validation failed")
                engine_output = engine.fallback_logic(fallback_error, engine_input, decision_slot_id)
            except Exception as fallback_error:
                logger.critical(
                    f"ResumeAuditEngine fallback after output validation failed: {str(fallback_error)}",
                    exc_info=True
                )
                return Response(
                    {
                        'error': 'Output validation failed',
                        'message': 'Engine output does not conform to schema and fallback failed',
                        'engine': 'ResumeAuditEngine',
                        'contract_version': CONTRACT_VERSION,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Persist signals to OS-native ATS Signals layer
        try:
            # Extract user_id from request for permission checks
            user_id = str(request.user.id) if request.user.is_authenticated else None
            signal_ids = persist_engine_signals(engine_output, decision_slot_id, user_id=user_id)
            logger.info(
                f"Persisted {len(signal_ids)} signals for decision_slot_id: {decision_slot_id}",
                extra={
                    'decision_slot_id': decision_slot_id,
                    'signals_count': len(signal_ids),
                    'user_id': request.user.id,
                }
            )
            
            # Trigger signal delivery handlers for critical signals
            for signal_id in signal_ids:
                try:
                    on_signal_created(str(signal_id))
                except Exception as e:
                    # Log but don't fail the request if signal delivery handler fails
                    logger.warning(
                        f"Signal delivery handler failed for signal {signal_id}: {str(e)}",
                        exc_info=True
                    )
                    
        except Exception as e:
            # Log persistence error but don't fail the request
            # The engine output is still valid and returned to the client
            logger.error(
                f"Failed to persist signals for decision_slot_id {decision_slot_id}: {str(e)}",
                exc_info=True,
                extra={
                    'decision_slot_id': decision_slot_id,
                    'user_id': request.user.id,
                }
            )
        
        # Get trace metadata (Rules 9 & 10: Cost Awareness & Traceability)
        trace_metadata = engine.trace_metadata()
        
        # Build response
        response_data = {
            'engine': 'ResumeAuditEngine',
            'contract_version': CONTRACT_VERSION,
            'engine_output': engine_output,
            'trace': trace_metadata,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.critical(
            f"Unexpected error in resume_audit_view: {str(e)}",
            exc_info=True,
            extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
            }
        )
        return Response(
            {
                'error': 'Internal server error',
                'message': 'An unexpected error occurred',
                'engine': 'ResumeAuditEngine',
                'contract_version': CONTRACT_VERSION,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

