# GateAI Migration - Quick Reference Rename Map

**Quick lookup table for all identity changes**

## Directory/Folder Renames

```
CareerBridge/                    → GateAI/
careerbridge/                    → gateai/
careerbridge/careerbridge/       → gateai/gateai/
careerbridge/resumes/            → gateai/ats_signals/
careerbridge/mentors/            → gateai/human_loop/
careerbridge/appointments/       → gateai/decision_slots/
careerbridge/notifications/      → gateai/signal_delivery/
JobCrawler/                      → JobIngestionEngine/
ResumeMatcher/                   → SignalCore/
```

## Python Import Path Changes

```python
# OLD                                    # NEW
from careerbridge.settings import *     from gateai.settings import *
from careerbridge.urls import *         from gateai.urls import *
import careerbridge.wsgi                import gateai.wsgi
import careerbridge.asgi                import gateai.asgi
import careerbridge.celery              import gateai.celery

from resumes import *                   from ats_signals import *
from resumes.models import Resume       from ats_signals.models import Resume
from resumes.views import *             from ats_signals.views import *

from mentors import *                   from human_loop import *
from mentors.models import Mentor       from human_loop.models import Mentor

from appointments import *              from decision_slots import *
from appointments.models import *       from decision_slots.models import *

from notifications import *             from signal_delivery import *
from notifications.models import *      from signal_delivery.models import *
```

## Django Configuration Changes

```python
# OLD                                    # NEW
DJANGO_SETTINGS_MODULE                  DJANGO_SETTINGS_MODULE
= 'careerbridge.settings'               = 'gateai.settings'

ROOT_URLCONF                            ROOT_URLCONF
= 'careerbridge.urls'                   = 'gateai.urls'

WSGI_APPLICATION                        WSGI_APPLICATION
= 'careerbridge.wsgi.application'       = 'gateai.wsgi.application'

ASGI_APPLICATION                        ASGI_APPLICATION
= 'careerbridge.asgi.application'       = 'gateai.asgi.application'

INSTALLED_APPS = [                      INSTALLED_APPS = [
    'resumes',                              'ats_signals',
    'mentors',                              'human_loop',
    'appointments',                         'decision_slots',
    'notifications',                        'signal_delivery',
]                                       ]

app = Celery("careerbridge")            app = Celery("gateai")
```

## API Endpoint Changes

```
# OLD                                    # NEW (with redirect)
/api/v1/resumes/                        /api/v1/ats-signals/
/api/v1/mentors/                        /api/v1/human-loop/
/api/v1/appointments/                   /api/v1/decision-slots/
/api/v1/notifications/                  /api/v1/signal-delivery/

# API Documentation
title: "CareerBridge API"               title: "GateAI API"
contact: contact@careerbridge.com       contact: contact@gateai.com
```

## Frontend Route Changes

```
# OLD                                    # NEW (with redirect)
/resumes                                /ats-signals
/resumes/:id/analysis                   /ats-signals/:id/analysis
/mentors                                /human-loop
/mentors/:id                            /human-loop/:id
/appointments                           /decision-slots
/appointments/:id                       /decision-slots/:id
/student/resumes                        /student/ats-signals
/student/appointments                   /student/decision-slots
/mentor/appointments                    /mentor/decision-slots
```

## Environment Variables

```
# OLD                                    # NEW (with backward compat)
DB_NAME=careerbridge                    DB_NAME=gateai
POSTGRES_DB=careerbridge                POSTGRES_DB=gateai
POSTGRES_USER=careerbridge_user         POSTGRES_USER=gateai_user

JOB_CRAWLER_BASE_URL                    JOB_INGESTION_ENGINE_BASE_URL
JOB_CRAWLER_API_KEY                     JOB_INGESTION_ENGINE_API_KEY
RESUME_MATCHER_BASE_URL                 SIGNAL_CORE_BASE_URL
RESUME_MATCHER_API_KEY                  SIGNAL_CORE_API_KEY

EMAIL_FROM=noreply@careerbridge.com     EMAIL_FROM=noreply@gateai.com
EMAIL_FROM_NAME=CareerBridge            EMAIL_FROM_NAME=GateAI
```

## Docker Service Names

```yaml
# docker-compose.prod.yml
# OLD                                    # NEW
services:                                services:
  careerbridge:                            gateai:
  jobcrawler:                              job_ingestion_engine:
  resumematcher:                           signal_core:

networks:                                networks:
  careerbridge_network:                    gateai_network:
```

## Semantic Name Changes (Conceptual)

| Old Concept | New Concept | Django App | API Path |
|------------|-------------|------------|----------|
| Resume Analyzer | ATS Signal Engine | `ats_signals` | `/api/v1/ats-signals/` |
| ResumeMatcher | Signal Core | (External Service) | `/signal-core/` |
| JobCrawler | Job Ingestion Engine | (External Service) | `/job-ingestion-engine/` |
| Mentor Market | Human-in-the-loop Layer | `human_loop` | `/api/v1/human-loop/` |
| Booking / Slot | Decision Slot System | `decision_slots` | `/api/v1/decision-slots/` |
| Notification | Signal Delivery Layer | `signal_delivery` | `/api/v1/signal-delivery/` |
| CareerBridge Platform | GateAI Platform | `gateai` | (root) |

## Frontend Component Prop Types

```typescript
// OLD                                    // NEW
interface ResumeProps {                  interface ATSSignalProps {
  resume: Resume;                          atsSignal: Resume;
  resumeId: number;                        atsSignalId: number;
}                                       }

interface AppointmentProps {             interface DecisionSlotProps {
  appointment: Appointment;                 decisionSlot: Appointment;
  appointmentId: number;                    decisionSlotId: number;
}                                       }
```

## External Service Client Classes

```python
# OLD                                    # NEW
JobCrawlerServiceClient                  JobIngestionEngineClient
ResumeMatcherServiceClient               SignalCoreServiceClient
JobCrawlerConfig                         JobIngestionEngineConfig
ResumeMatcherConfig                      SignalCoreConfig
```

## Frontend Service Files

```
# File paths (same locations, different imports)
frontend/src/services/api/resumeService.ts
  → Update imports: from 'resumes' → from 'ats_signals'
  
frontend/src/services/api/appointmentService.ts
  → Update imports: from 'appointments' → from 'decision_slots'
```

## Documentation Updates

All references in:
- `README.md`
- `QUICKSTART.md`
- `DEPLOYMENT.md`
- `docs/*.md`

Change: `CareerBridge` → `GateAI`

---

**See MIGRATION_PLAN_PHASE_A.md for detailed migration strategy and commit sequence.**

