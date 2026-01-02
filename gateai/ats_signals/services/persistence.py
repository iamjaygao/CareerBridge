"""
Signal persistence service for ATS Signals layer.

Maps engine outputs to OS-native ATS Signal models and persists them to the database.
Maintains signal integrity by anchoring all signals to DecisionSlot IDs.

Rule 15: SIGNAL INTEGRITY - Every signal MUST be anchored to a DecisionSlot ID.
"""

import logging
from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone

from ats_signals.models import ATSSignal

logger = logging.getLogger(__name__)

# Signal schema version for versioning
SIGNAL_SCHEMA_VERSION = "1.0.0"


def persist_engine_signals(engine_output: dict, decision_slot_id: str, user_id: str = None) -> List[int]:
    """
    Persist engine signals to the database.
    
    Maps engine output signals to ATSSignal model and saves them with proper
    DecisionSlot ID anchoring.
    
    Args:
        engine_output: Engine output dictionary containing 'signals' list
        decision_slot_id: DecisionSlot ID to anchor all signals (Rule 15: SIGNAL INTEGRITY)
        user_id: Optional user ID to store in signal details for permission checks
        
    Returns:
        List of created signal IDs
        
    Raises:
        ValueError: If decision_slot_id is invalid
        Exception: If persistence fails (transaction will rollback)
    """
    # Validate decision_slot_id (Rule 15)
    if not decision_slot_id or not isinstance(decision_slot_id, str) or len(decision_slot_id.strip()) == 0:
        raise ValueError("Invalid decision_slot_id: must be non-empty string")
    
    # Extract signals from engine output
    signals_data = engine_output.get('signals', [])
    if not signals_data:
        logger.info(f"No signals to persist for decision_slot_id: {decision_slot_id}")
        return []
    
    # Extract engine metadata
    engine_name = 'ResumeAuditEngine'  # Engine name is known from context
    engine_version = engine_output.get('engine_version', '1.0.0')
    
    # Use atomic transaction for persistence
    created_signal_ids = []
    
    try:
        with transaction.atomic():
            for signal_data in signals_data:
                # Map engine signal to ATSSignal model
                # Include user_id in signal details for permission checks
                signal_details = signal_data.get('details', {}).copy()
                if user_id:
                    signal_details['user_id'] = str(user_id)
                
                ats_signal = ATSSignal(
                    decision_slot_id=decision_slot_id,  # Rule 15: SIGNAL INTEGRITY
                    signal_type=signal_data.get('signal_type'),
                    severity=signal_data.get('severity'),
                    category=signal_data.get('category'),
                    message=signal_data.get('message'),
                    details=signal_details,  # Include user_id for permission checks
                    section=signal_data.get('section'),
                    line_number=signal_data.get('line_number'),
                    engine_name=engine_name,
                    engine_version=engine_version,
                    signal_schema_version=SIGNAL_SCHEMA_VERSION,
                )
                
                # Validate required fields before save
                if not ats_signal.signal_type:
                    logger.warning(f"Skipping signal with missing signal_type for decision_slot_id: {decision_slot_id}")
                    continue
                
                if not ats_signal.severity:
                    logger.warning(f"Skipping signal with missing severity for decision_slot_id: {decision_slot_id}")
                    continue
                
                if not ats_signal.message:
                    logger.warning(f"Skipping signal with missing message for decision_slot_id: {decision_slot_id}")
                    continue
                
                # Save signal
                ats_signal.save()
                created_signal_ids.append(ats_signal.id)
                
                logger.debug(
                    f"Persisted signal {ats_signal.id} for decision_slot_id {decision_slot_id}",
                    extra={
                        'signal_id': ats_signal.id,
                        'decision_slot_id': decision_slot_id,
                        'signal_type': ats_signal.signal_type,
                        'severity': ats_signal.severity,
                    }
                )
            
            logger.info(
                f"Persisted {len(created_signal_ids)} signals for decision_slot_id: {decision_slot_id}",
                extra={
                    'decision_slot_id': decision_slot_id,
                    'signals_count': len(created_signal_ids),
                    'engine_name': engine_name,
                }
            )
            
    except Exception as e:
        logger.error(
            f"Failed to persist signals for decision_slot_id {decision_slot_id}: {str(e)}",
            exc_info=True,
            extra={
                'decision_slot_id': decision_slot_id,
                'signals_count': len(signals_data),
            }
        )
        raise
    
    # Verify all signals are anchored to decision_slot_id (Rule 15)
    persisted_signals = ATSSignal.objects.filter(id__in=created_signal_ids)
    for signal in persisted_signals:
        if signal.decision_slot_id != decision_slot_id:
            logger.error(
                f"Signal integrity violation: Signal {signal.id} has decision_slot_id {signal.decision_slot_id}, "
                f"expected {decision_slot_id}",
                extra={
                    'signal_id': signal.id,
                    'expected_decision_slot_id': decision_slot_id,
                    'actual_decision_slot_id': signal.decision_slot_id,
                }
            )
            raise ValueError(
                f"Signal integrity violation: Signal {signal.id} not properly anchored to DecisionSlot {decision_slot_id}"
            )
    
    return created_signal_ids


def get_signals_by_decision_slot(decision_slot_id: str) -> List[ATSSignal]:
    """
    Retrieve all signals for a given DecisionSlot ID.
    
    Args:
        decision_slot_id: DecisionSlot ID to query
        
    Returns:
        List of ATSSignal objects
    """
    return list(ATSSignal.objects.filter(decision_slot_id=decision_slot_id).order_by('-created_at'))


def get_critical_signals(decision_slot_id: str = None) -> List[ATSSignal]:
    """
    Retrieve critical severity signals.
    
    Args:
        decision_slot_id: Optional DecisionSlot ID to filter by
        
    Returns:
        List of critical ATSSignal objects
    """
    queryset = ATSSignal.objects.filter(severity='critical')
    if decision_slot_id:
        queryset = queryset.filter(decision_slot_id=decision_slot_id)
    return list(queryset.order_by('-created_at'))


# Re-export permission functions for convenience
from ats_signals.permissions import filter_signals_by_ownership, user_can_access_decision_slot

