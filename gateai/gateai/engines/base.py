"""
GateAI OS Engine Base Class

Kernel infrastructure for engine plug-ins.
All engines MUST inherit from BaseEngine.

This module provides the abstract base class that defines the engine contract:
- Input/Output schema validation (Pydantic)
- Execution interface (run method)
- Resilience (fallback_logic)
- Traceability (trace_metadata)
- Output validation

No business logic. No LLM calls. Kernel infrastructure only.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError


class BaseEngine(ABC):
    """
    Abstract base class for all GateAI engines.
    
    All engines MUST inherit from this class and implement:
    - input_schema: Pydantic model for input validation
    - output_schema: Pydantic model for output validation
    - run(): Main execution method
    - fallback_logic(): Resilience mechanism
    - trace_metadata(): Traceability metadata
    
    Rule 14: AUTOMATED CONTRACT TESTING
    - Every engine MUST define a Pydantic schema.
    - All outputs MUST pass schema validation.
    
    Rule 15: SIGNAL INTEGRITY
    - Every engine output MUST be anchored to a DecisionSlot ID.
    - No floating signals allowed.
    """
    
    # Abstract class variables - must be defined by subclasses
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    
    @abstractmethod
    def run(self, raw_input: dict, decision_slot_id: str) -> dict:
        """
        Execute the engine with raw input and decision slot ID.
        
        Args:
            raw_input: Raw input dictionary (will be validated against input_schema)
            decision_slot_id: DecisionSlot ID to anchor the output (Rule 15: SIGNAL INTEGRITY)
            
        Returns:
            dict: Output dictionary (must conform to output_schema)
            
        Raises:
            ValidationError: If input doesn't conform to input_schema
            Exception: Engine-specific errors (should trigger fallback_logic)
        """
        pass
    
    @abstractmethod
    def fallback_logic(self, error: Exception, raw_input: dict, decision_slot_id: str) -> dict:
        """
        Resilience mechanism - called when run() fails.
        
        Args:
            error: The exception that triggered the fallback
            raw_input: Original input that caused the failure
            decision_slot_id: DecisionSlot ID for signal integrity
            
        Returns:
            dict: Fallback output (must conform to output_schema)
            
        Rule 7: Resilience (fallback_logic required)
        """
        pass
    
    @abstractmethod
    def trace_metadata(self) -> Dict[str, Any]:
        """
        Return traceability metadata for the last execution.
        
        Returns:
            dict with keys:
                - latency_ms: int - Execution latency in milliseconds
                - tokens_used: Optional[int] - Tokens consumed (if applicable)
                - model_version: Optional[str] - Model version used (if applicable)
                
        Rule 9: Cost Awareness
        Rule 10: Traceability
        """
        pass
    
    def validate_output(self, output: dict) -> bool:
        """
        Validate output against output_schema.
        
        Args:
            output: Output dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If output doesn't conform to output_schema
            
        Rule 14: AUTOMATED CONTRACT TESTING
        """
        try:
            self.output_schema(**output)
            return True
        except ValidationError:
            return False
    
    def validate_input(self, raw_input: dict) -> bool:
        """
        Validate input against input_schema.
        
        Args:
            raw_input: Input dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If input doesn't conform to input_schema
        """
        try:
            self.input_schema(**raw_input)
            return True
        except ValidationError:
            return False

