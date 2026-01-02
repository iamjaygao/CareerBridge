# GateAI OS Contract

**Version**: 1.0.1  
**Status**: Active  
**Last Updated**: 2026-01-01

---

## Platform Definition

**GateAI** is an **AI Operating System (AI OS)** - a platform that orchestrates AI-powered signals, human expertise, decision workflows, and delivery mechanisms to enable intelligent career development.

Unlike a traditional application, GateAI operates as a foundational OS layer that:
- Provides core AI signal processing capabilities
- Integrates human judgment through structured loops
- Manages decision-making workflows
- Delivers signals and insights through standardized channels

---

## OS Core Layers

GateAI consists of four foundational layers that define the platform's architecture:

### 1. ATS Signal Bus (`ats_signals`)
**Purpose**: OS-level signal routing, storage, and validation  
**Former Name**: Resume Analyzer  
**API Namespace**: `/api/v1/ats-signals/`

**Role**:
This is a kernel-level signal bus. It does NOT run AI models.
All AI inference MUST be performed by pluggable external engines (e.g. Signal Core Engine).

**Responsibilities**:
- Accept structured signals from engines
- Validate signal schemas
- Persist signals via decision_slots
- Provide API access to stored signals
- Enforce auditability and traceability

**Layer Type**: Kernel Signal Bus


---

### 2. Human-in-the-loop Layer (`human_loop`)
**Purpose**: Structured human expertise integration  
**Former Name**: Mentor Market  
**API Namespace**: `/api/v1/human-loop/`

**Capabilities**:
- Expert mentor discovery and matching
- Mentor-student connection workflows
- Expert feedback and guidance systems
- Human expertise routing
- Professional network orchestration

**Layer Type**: Human Integration

---

### 3. Decision Slot System (`decision_slots`)
**Purpose**: Decision workflow orchestration  
**Former Name**: Booking / Slot System  
**API Namespace**: `/api/v1/decision-slots/`

**Capabilities**:
- Time slot management
- Appointment booking workflows
- Decision point scheduling
- Resource allocation
- Commitment tracking

**Layer Type**: Workflow Orchestration

---

### 4. Signal Delivery Layer (`signal_delivery`)
**Purpose**: Multi-channel signal delivery and notification  
**Former Name**: Notification System  
**API Namespace**: `/api/v1/signal-delivery/`

**Capabilities**:
- Multi-channel notification delivery
- Signal routing and prioritization
- Delivery status tracking
- User preference management
- Delivery analytics

**Layer Type**: Delivery Infrastructure

---

## Official OS API Namespaces

GateAI exposes standardized API endpoints for each OS layer:

### Core Layer APIs

```
/api/v1/ats-signals/        - ATS Signal Engine
/api/v1/human-loop/         - Human-in-the-loop Layer
/api/v1/decision-slots/     - Decision Slot System
/api/v1/signal-delivery/    - Signal Delivery Layer
```

**Access**: All core layer APIs are available to authenticated users with appropriate permissions.

**Versioning**: Current version is `v1`. Future breaking changes will increment to `v2`.

---

## Engine Infrastructure

GateAI provides kernel-level infrastructure for pluggable engine implementations. All external engines MUST conform to the BaseEngine contract.

### BaseEngine Contract

**Location**: `gateai.gateai.engines.base.BaseEngine`  
**Type**: Abstract Base Class (ABC)  
**Purpose**: Kernel infrastructure for engine plug-ins

**Contract Requirements**:

All engines MUST inherit from `BaseEngine` and implement:

1. **Schema Definitions** (Pydantic models):
   - `input_schema`: Pydantic model for input validation
   - `output_schema`: Pydantic model for output validation

2. **Execution Method**:
   - `run(raw_input: dict, decision_slot_id: str) -> dict`
     - Executes engine logic with validated input
     - MUST anchor output to DecisionSlot ID (Rule 15: SIGNAL INTEGRITY)
     - Returns output conforming to `output_schema`

3. **Resilience Mechanism**:
   - `fallback_logic(error: Exception, raw_input: dict, decision_slot_id: str) -> dict`
     - Called when `run()` fails
     - MUST return valid output conforming to `output_schema` (Rule 7: Resilience)

4. **Traceability**:
   - `trace_metadata() -> Dict[str, Any]`
     - Returns: `{latency_ms: int, tokens_used: Optional[int], model_version: Optional[str]}`
     - Enables cost awareness and traceability (Rules 9 & 10)

5. **Validation Methods** (provided by BaseEngine):
   - `validate_input(raw_input: dict) -> bool`
   - `validate_output(output: dict) -> bool`

**Engine Rules** (from .cursorrules):

- **Rule 4**: All engines MUST inherit BaseEngine
- **Rule 5**: Input/Output Isolation
- **Rule 6**: No Direct DB Access
- **Rule 7**: Resilience (fallback_logic required)
- **Rule 8**: Hallucination Guard
- **Rule 9**: Cost Awareness
- **Rule 10**: Traceability
- **Rule 14**: AUTOMATED CONTRACT TESTING - Every engine MUST define a Pydantic schema. All outputs MUST pass schema validation.
- **Rule 15**: SIGNAL INTEGRITY - Every engine output MUST be anchored to a DecisionSlot ID. No floating signals allowed.

**Import Path**:
```python
from gateai.gateai.engines import BaseEngine
```

**Kernel Infrastructure Only**:
- BaseEngine contains NO business logic
- BaseEngine contains NO LLM calls
- BaseEngine is pure kernel infrastructure for engine plug-ins

---

## External Engine Slots (Reserved)

GateAI reserves namespace slots for external engines that may be integrated in the future. These slots are **reserved but not currently implemented**.

### Reserved Engine Namespaces

```
/api/engines/signal-core/       - Reserved for Signal Core Engine
/api/engines/job-ingestion/     - Reserved for Job Ingestion Engine
```

**Status**: Placeholder routes only - no implementation exists  
**Purpose**: 
- Ensure namespace availability for future engine integrations
- Maintain consistent API structure
- Prevent namespace conflicts

**Future Integration**:
- Signal Core Engine may replace or augment current signal processing
- Job Ingestion Engine may provide enhanced job market data ingestion
- All future engines MUST inherit from `BaseEngine` (see Engine Infrastructure section)
- Integration will be documented in future contract updates

**Note**: These routes currently return 404. Do not depend on them until officially implemented.

---

## Backward Compatibility Policy

GateAI maintains backward compatibility for legacy API paths and namespaces during a **6-month deprecation window**.

### Legacy API Paths (Redirected)

The following legacy paths redirect to new OS API namespaces:

| Legacy Path | New Path | Status |
|------------|----------|--------|
| `/api/v1/resumes/` | `/api/v1/ats-signals/` | ✅ Redirecting (deprecated) |
| `/api/v1/mentors/` | `/api/v1/human-loop/` | ✅ Redirecting (deprecated) |
| `/api/v1/appointments/` | `/api/v1/decision-slots/` | ✅ Redirecting (deprecated) |
| `/api/v1/notifications/` | `/api/v1/signal-delivery/` | ✅ Redirecting (deprecated) |

**Redirect Behavior**:
- HTTP 302 (Temporary Redirect) - indicates path may change
- Redirects are non-permanent to allow future removal
- All redirects maintain request method, headers, and body

**Deprecation Timeline**:
- **Phase 1** (Months 1-3): Legacy paths redirect with deprecation warnings
- **Phase 2** (Months 4-6): Enhanced deprecation warnings, documentation updates
- **Phase 3** (Month 7+): Legacy paths may be removed (separate migration required)

### Legacy Python Imports (Shadow Modules)

Legacy Python import paths are available through compatibility shims:

| Legacy Import | New Import | Status |
|--------------|------------|--------|
| `from careerbridge import *` | `from gateai import *` | ✅ DeprecationWarning |
| `from resumes import *` | `from ats_signals import *` | ✅ DeprecationWarning |
| `from mentors import *` | `from human_loop import *` | ✅ DeprecationWarning |
| `from appointments import *` | `from decision_slots import *` | ✅ DeprecationWarning |
| `from notifications import *` | `from signal_delivery import *` | ✅ DeprecationWarning |

**Behavior**:
- Imports work but emit `DeprecationWarning`
- Warnings include guidance on new import paths
- Shadow modules will be removed after deprecation window

---

## OS Principles

### 1. Layer Independence
Each OS layer operates independently with defined interfaces. Layers communicate through:
- Standardized API contracts
- Event-driven signaling
- Shared data models (when appropriate)

### 2. Backward Compatibility
OS changes maintain backward compatibility during deprecation windows to ensure:
- Gradual migration paths
- Zero-downtime transitions
- Developer adoption time

### 3. Namespace Reservation
External engine namespaces are reserved proactively to:
- Prevent conflicts
- Enable future expansion
- Maintain consistent API structure

### 4. API Versioning
OS APIs use semantic versioning:
- `/api/v1/*` - Current stable version
- Future breaking changes increment to `/api/v2/*`
- Minor changes maintain backward compatibility

### 5. Signal-First Architecture
GateAI prioritizes signal processing and delivery:
- Signals flow through standardized channels
- Human judgment integrates at defined points
- Decisions are tracked and auditable

### 6. Engine Plug-In Architecture
GateAI provides kernel infrastructure for pluggable engines:
- All engines MUST inherit from `BaseEngine`
- Engines are isolated from kernel code (no direct DB access)
- Engine contracts enforce schema validation and signal integrity
- Engines provide resilience through fallback mechanisms
- Engine execution is traceable and cost-aware

---

## Integration Guidelines

### For Frontend Applications

**Use OS APIs directly**:
```typescript
// Preferred: Use OS API namespaces
GET /api/v1/ats-signals/
GET /api/v1/human-loop/
GET /api/v1/decision-slots/
GET /api/v1/signal-delivery/
```

**Handle redirects gracefully**:
- Legacy paths may redirect to new paths
- Update clients to use new paths proactively
- Don't rely on redirects for production workloads

### For External Services

**Do NOT use reserved engine namespaces**:
- `/api/engines/signal-core/` - Reserved, not available
- `/api/engines/job-ingestion/` - Reserved, not available

**Use current OS APIs**:
- Integrate with `/api/v1/ats-signals/` for signal processing
- Integrate with `/api/v1/human-loop/` for human expertise
- Integrate with `/api/v1/decision-slots/` for workflow orchestration

### For Python Code

**Use new import paths**:
```python
# Preferred
from gateai import settings
from ats_signals.models import Resume
from human_loop.models import MentorProfile
from decision_slots.models import Appointment
from signal_delivery.models import Notification
from gateai.gateai.engines import BaseEngine  # Engine infrastructure
```

**Legacy imports deprecated**:
```python
# Deprecated (will be removed)
from careerbridge import settings  # ❌ DeprecationWarning
from resumes.models import Resume  # ❌ DeprecationWarning
```

### For Engine Developers

**Implementing a new engine**:
```python
from gateai.gateai.engines import BaseEngine
from pydantic import BaseModel

class MyEngineInput(BaseModel):
    """Input schema for MyEngine"""
    field1: str
    field2: int

class MyEngineOutput(BaseModel):
    """Output schema for MyEngine"""
    result: str
    confidence: float

class MyEngine(BaseEngine):
    """Example engine implementation"""
    
    input_schema = MyEngineInput
    output_schema = MyEngineOutput
    
    def run(self, raw_input: dict, decision_slot_id: str) -> dict:
        # Validate input
        validated_input = self.input_schema(**raw_input)
        
        # Engine logic here (no direct DB access, Rule 6)
        result = self._process(validated_input)
        
        # Return output anchored to decision_slot_id (Rule 15)
        return {
            "result": result,
            "confidence": 0.95,
            "decision_slot_id": decision_slot_id
        }
    
    def fallback_logic(self, error: Exception, raw_input: dict, decision_slot_id: str) -> dict:
        # Resilience mechanism (Rule 7)
        return {
            "result": "fallback_value",
            "confidence": 0.0,
            "decision_slot_id": decision_slot_id,
            "error": str(error)
        }
    
    def trace_metadata(self) -> Dict[str, Any]:
        # Traceability (Rules 9 & 10)
        return {
            "latency_ms": 150,
            "tokens_used": 1000,
            "model_version": "gpt-4-turbo"
        }
    
    def _process(self, input_data):
        # Internal processing logic
        pass
```

---

## Migration Path

### For API Consumers

1. **Identify legacy endpoints** in your codebase
2. **Update API calls** to use new OS namespaces
3. **Test redirect behavior** to ensure compatibility
4. **Monitor deprecation warnings** in logs
5. **Complete migration** before deprecation window ends

### For Python Developers

1. **Identify legacy imports** in your codebase
2. **Update import statements** to use new paths
3. **Resolve deprecation warnings** during development
4. **Update tests** to use new import paths
5. **Complete migration** before shadow modules are removed

---

## Contract Changes

This contract may be updated to reflect:
- New OS layer additions
- External engine integrations
- API version updates
- Breaking changes (with advance notice)

**Change Process**:
- Contract updates require version increment
- Breaking changes require 3-month advance notice
- Deprecation timelines are documented

**Version History**:
- **v1.0.1** (2026-01-21): Kernel re-freeze - Added BaseEngine infrastructure documentation
  - Documented BaseEngine contract and requirements
  - Added engine infrastructure section
  - Clarified engine plug-in specifications
- **v1.0.0** (2026-01-21): Initial OS contract freeze

---

## Support and Questions

For questions about GateAI OS:
- **API Documentation**: See `/swagger/` for interactive API docs
- **Migration Guide**: See `docs/MIGRATION_PLAN_PHASE_A.md`
- **Technical Support**: Contact platform team

---

**END OF GATEAI OS CONTRACT**

*This contract defines the stable API surface for GateAI OS. Changes to this contract follow the documented change process.*

