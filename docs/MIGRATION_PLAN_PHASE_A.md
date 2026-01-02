# GateAI Identity Migration Plan - Phase A (Planning Only)

**Status**: Planning Phase - No Code Changes  
**Date**: 2026-01-21 
**Migration Type**: System Identity Migration (CareerBridge → GateAI)

---

## Executive Summary

This document provides a comprehensive planning map for migrating the CareerBridge platform to GateAI. This is a **SYSTEM IDENTITY MIGRATION**, focusing on renaming and rebranding while maintaining all business logic, APIs, and database schemas.

**Key Constraints**:
- ✅ NO business logic changes
- ✅ NO new features
- ✅ NO database schema modifications
- ✅ NO deletion of existing APIs
- ✅ Backward compatibility required

---

## 1. Comprehensive Rename Map

### 1.1 Directory/Folder Structure

| Old Path | New Path | Type | Impact |
|----------|----------|------|--------|
| `CareerBridge/` (root) | `GateAI/` | Root directory | High - Git repo, CI/CD |
| `careerbridge/` | `gateai/` | Django project root | **CRITICAL** - Python package |
| `careerbridge/careerbridge/` | `gateai/gateai/` | Django config package | **CRITICAL** - Settings module |
| `careerbridge/resumes/` | `gateai/ats_signals/` | Django app | **CRITICAL** - Major module rename |
| `careerbridge/mentors/` | `gateai/human_loop/` | Django app | **CRITICAL** - Semantic rename |
| `careerbridge/appointments/` | `gateai/decision_slots/` | Django app | **CRITICAL** - Semantic rename |
| `careerbridge/notifications/` | `gateai/signal_delivery/` | Django app | **CRITICAL** - Semantic rename |
| `JobCrawler/` | `JobIngestionEngine/` | External service | Medium - Service rename |
| `ResumeMatcher/` | `SignalCore/` | External service | Medium - Service rename |
| `frontend/src/pages/resumes/` | `frontend/src/pages/ats-signals/` | Frontend pages | Medium |
| `frontend/src/pages/mentors/` | `frontend/src/pages/human-loop/` | Frontend pages | Medium |
| `frontend/src/pages/appointments/` | `frontend/src/pages/decision-slots/` | Frontend pages | Medium |

### 1.2 Python Package/Module Names

| Old Import Path | New Import Path | Files Affected (est.) |
|----------------|-----------------|----------------------|
| `careerbridge.settings` | `gateai.settings` | 15+ (manage.py, wsgi.py, asgi.py, celery.py, scripts) |
| `careerbridge.urls` | `gateai.urls` | 5+ |
| `careerbridge.wsgi` | `gateai.wsgi` | 2 |
| `careerbridge.asgi` | `gateai.asgi` | 2 |
| `careerbridge.celery` | `gateai.celery` | 10+ (Celery tasks) |
| `careerbridge.external_services.*` | `gateai.external_services.*` | 15+ |
| `resumes.*` | `ats_signals.*` | 50+ (models, views, serializers, services, urls) |
| `mentors.*` | `human_loop.*` | 40+ |
| `appointments.*` | `decision_slots.*` | 35+ |
| `notifications.*` | `signal_delivery.*` | 25+ |
| `from careerbridge import` | `from gateai import` | 30+ |

### 1.3 Django Configuration Keys

| Old Setting | New Setting | Location |
|------------|-------------|----------|
| `DJANGO_SETTINGS_MODULE=careerbridge.settings` | `DJANGO_SETTINGS_MODULE=gateai.settings` | manage.py, wsgi.py, asgi.py, celery.py, pytest.ini |
| `ROOT_URLCONF = 'careerbridge.urls'` | `ROOT_URLCONF = 'gateai.urls'` | settings_base.py |
| `WSGI_APPLICATION = 'careerbridge.wsgi.application'` | `WSGI_APPLICATION = 'gateai.wsgi.application'` | settings_base.py |
| `ASGI_APPLICATION = 'careerbridge.asgi.application'` | `ASGI_APPLICATION = 'gateai.asgi.application'` | settings_base.py |
| `INSTALLED_APPS = ['resumes', ...]` | `INSTALLED_APPS = ['ats_signals', ...]` | settings_base.py |
| `INSTALLED_APPS = ['mentors', ...]` | `INSTALLED_APPS = ['human_loop', ...]` | settings_base.py |
| `INSTALLED_APPS = ['appointments', ...]` | `INSTALLED_APPS = ['decision_slots', ...]` | settings_base.py |
| `INSTALLED_APPS = ['notifications', ...]` | `INSTALLED_APPS = ['signal_delivery', ...]` | settings_base.py |
| `app = Celery("careerbridge")` | `app = Celery("gateai")` | celery.py |
| `CELERY_IMPORTS = ('appointments.tasks', ...)` | `CELERY_IMPORTS = ('decision_slots.tasks', ...)` | settings_base.py |

### 1.4 API Endpoints (URL Patterns)

| Old API Path | New API Path | Backward Compat? | Location |
|-------------|--------------|------------------|----------|
| `/api/v1/resumes/` | `/api/v1/ats-signals/` | ✅ Redirect | urls.py |
| `/api/v1/mentors/` | `/api/v1/human-loop/` | ✅ Redirect | urls.py |
| `/api/v1/appointments/` | `/api/v1/decision-slots/` | ✅ Redirect | urls.py |
| `/api/v1/notifications/` | `/api/v1/signal-delivery/` | ✅ Redirect | urls.py |
| API docs title: "CareerBridge API" | "GateAI API" | - | urls.py (Swagger) |
| API contact: "contact@careerbridge.com" | "contact@gateai.com" | - | urls.py |

### 1.5 Frontend Routes

| Old Route | New Route | Component Location |
|----------|-----------|-------------------|
| `/resumes` | `/ats-signals` | App.tsx, routing |
| `/resumes/:id/analysis` | `/ats-signals/:id/analysis` | App.tsx |
| `/mentors` | `/human-loop` | App.tsx |
| `/mentors/:id` | `/human-loop/:id` | App.tsx |
| `/appointments` | `/decision-slots` | App.tsx |
| `/appointments/:id` | `/decision-slots/:id` | App.tsx |
| `/student/resumes` | `/student/ats-signals` | App.tsx |
| `/student/appointments` | `/student/decision-slots` | App.tsx |
| `/mentor/appointments` | `/mentor/decision-slots` | App.tsx |

### 1.6 Environment Variables

| Old Variable | New Variable | Keep Old? | Files |
|-------------|--------------|-----------|-------|
| `DB_NAME=careerbridge` | `DB_NAME=gateai` | ⚠️ Keep both | env_template.txt, docker-compose |
| `POSTGRES_DB=careerbridge` | `POSTGRES_DB=gateai` | ⚠️ Keep both | docker-compose.prod.yml |
| `POSTGRES_USER=careerbridge_user` | `POSTGRES_USER=gateai_user` | ⚠️ Keep both | docker-compose.prod.yml |
| `JOB_CRAWLER_*` | `JOB_INGESTION_ENGINE_*` | ✅ Deprecate old | env_template.txt, config.py |
| `RESUME_MATCHER_*` | `SIGNAL_CORE_*` | ✅ Deprecate old | env_template.txt, config.py |
| `EMAIL_FROM=noreply@careerbridge.com` | `EMAIL_FROM=noreply@gateai.com` | - | config.py |
| `EMAIL_FROM_NAME=CareerBridge` | `EMAIL_FROM_NAME=GateAI` | - | config.py |

### 1.7 Docker/Infrastructure

| Old Name | New Name | File |
|----------|----------|------|
| Service: `careerbridge` | `gateai` | docker-compose.prod.yml |
| Service: `jobcrawler` | `job_ingestion_engine` | docker-compose.prod.yml |
| Service: `resumematcher` | `signal_core` | docker-compose.prod.yml |
| Network: `careerbridge_network` | `gateai_network` | docker-compose.prod.yml |
| Volume: `postgres_data` (DB name) | Same (keep DB name) | docker-compose.prod.yml |
| Upstream: `careerbridge` | `gateai` | deploy.sh (nginx.conf) |
| Upstream: `jobcrawler` | `job_ingestion_engine` | deploy.sh |
| Upstream: `resumematcher` | `signal_core` | deploy.sh |
| Nginx location: `/jobcrawler/` | `/job-ingestion-engine/` | deploy.sh |
| Nginx location: `/resumematcher/` | `/signal-core/` | deploy.sh |

### 1.8 Documentation Files

| Old File | New Content | Notes |
|----------|-------------|-------|
| `README.md` | Update all "CareerBridge" → "GateAI" | Keep structure |
| `QUICKSTART.md` | Update all references | Keep instructions |
| `DEPLOYMENT.md` | Update service names, paths | Keep procedures |
| `docs/PROJECT-COMPREHENSIVE-ANALYSIS.md` | Update title, references | Keep analysis |
| `docs/API.md` | Update API references | Keep API docs |
| `docs/DEVELOPMENT.md` | Update paths, names | Keep dev guide |
| All `docs/historical/*.md` | Update references | Historical context |

### 1.9 Frontend Configuration

| Old Reference | New Reference | Files |
|--------------|---------------|-------|
| `manifest.json`: "CareerBridge" | "GateAI" | frontend/public/manifest.json |
| `index.html`: title, meta | Update to GateAI | frontend/public/index.html |
| `MainLayout.tsx`: "CareerBridge" | "GateAI" | frontend/src/components/layout/ |
| Component props: `resume*` | `atsSignal*` | Type definitions, components |
| Component props: `appointment*` | `decisionSlot*` | Type definitions, components |
| API service imports | Update import paths | frontend/src/services/api/*.ts |

### 1.10 External Service Names (Semantic Updates)

| Old Service Name | New Service Name | Internal Namespace |
|-----------------|------------------|-------------------|
| Resume Analyzer | ATS Signal Engine | `ats_signals` |
| ResumeMatcher | Signal Core | `signal_core` (service), `SignalCore/` (folder) |
| JobCrawler | Job Ingestion Engine | `job_ingestion_engine` (service), `JobIngestionEngine/` (folder) |
| Mentor Market | Human-in-the-loop Layer | `human_loop` |
| Booking / Slot | Decision Slot System | `decision_slots` |
| Notification | Signal Delivery Layer | `signal_delivery` |
| Chrome Extension | GateAI Client | (Future - not in current codebase) |

---

## 2. Migration Strategy

### 2.1 Phase Approach

**Phase A: Planning** ✅ (Current)
- Complete rename mapping
- Risk assessment
- Compatibility strategy

**Phase B: Backend Core** (Django project structure)
- Rename `careerbridge/` → `gateai/`
- Update settings, wsgi, asgi, celery
- Update all imports

**Phase C: Django Apps**
- Rename apps: `resumes` → `ats_signals`, `mentors` → `human_loop`, etc.
- Update `INSTALLED_APPS`
- Update migrations (app_label only)
- Add URL redirects for backward compatibility

**Phase D: External Services**
- Rename `JobCrawler/` → `JobIngestionEngine/`
- Rename `ResumeMatcher/` → `SignalCore/`
- Update client configurations

**Phase E: Frontend**
- Update routes
- Update API service paths
- Update UI text and branding

**Phase F: Infrastructure**
- Update Docker services
- Update deployment scripts
- Update environment templates

**Phase G: Documentation**
- Update all markdown files
- Update API documentation
- Update deployment guides

**Phase H: Cleanup**
- Remove deprecated redirects (after grace period)
- Remove deprecated env var support
- Final verification

### 2.2 Commit Sequence Plan

```
Commit 1: [BACKEND] Rename Django project root careerbridge/ → gateai/
  - Rename directory
  - Update manage.py (DJANGO_SETTINGS_MODULE)
  - Update wsgi.py, asgi.py
  - Update celery.py
  - Update pytest.ini

Commit 2: [BACKEND] Rename Django config package careerbridge/careerbridge/ → gateai/gateai/
  - Rename directory
  - Update settings_base.py (ROOT_URLCONF, WSGI_APPLICATION, ASGI_APPLICATION)
  - Update all imports in external_services/*

Commit 3: [BACKEND] Add backward compatibility shims for imports
  - Create careerbridge/__init__.py (shadow module)
  - Re-export from gateai
  - Add deprecation warnings

Commit 4: [BACKEND] Rename Django app: resumes → ats_signals
  - Rename directory
  - Update apps.py (name, label)
  - Update INSTALLED_APPS in settings_base.py
  - Update all imports
  - Add URL redirect: /api/v1/resumes/ → /api/v1/ats-signals/

Commit 5: [BACKEND] Rename Django app: mentors → human_loop
  - (Same pattern as Commit 4)
  - URL redirect: /api/v1/mentors/ → /api/v1/human-loop/

Commit 6: [BACKEND] Rename Django app: appointments → decision_slots
  - (Same pattern as Commit 4)
  - URL redirect: /api/v1/appointments/ → /api/v1/decision-slots/

Commit 7: [BACKEND] Rename Django app: notifications → signal_delivery
  - (Same pattern as Commit 4)
  - URL redirect: /api/v1/notifications/ → /api/v1/signal-delivery/

Commit 8: [BACKEND] Update Celery task imports
  - Update CELERY_IMPORTS in settings_base.py
  - Update task decorators if needed

Commit 9: [BACKEND] Update external service clients
  - Update JobCrawler → JobIngestionEngine references
  - Update ResumeMatcher → SignalCore references
  - Update config.py class names

Commit 10: [BACKEND] Update API documentation metadata
  - Update Swagger title: "CareerBridge API" → "GateAI API"
  - Update contact email

Commit 11: [SERVICES] Rename JobCrawler/ → JobIngestionEngine/
  - Rename directory
  - Update internal references
  - Update Docker service name

Commit 12: [SERVICES] Rename ResumeMatcher/ → SignalCore/
  - Rename directory
  - Update internal references
  - Update Docker service name

Commit 13: [INFRA] Update Docker configuration
  - Update docker-compose.prod.yml (service names, networks)
  - Update deploy.sh (nginx upstream names)
  - Update environment variable references

Commit 14: [FRONTEND] Update API service imports and routes
  - Update frontend/src/services/api/*.ts (import paths)
  - Update frontend/src/App.tsx (route definitions)
  - Add route redirects for backward compatibility

Commit 15: [FRONTEND] Update UI branding and text
  - Update manifest.json
  - Update index.html
  - Update MainLayout, Headers, Footers
  - Update component prop types (resume → atsSignal, etc.)

Commit 16: [FRONTEND] Update frontend route paths
  - Update all page component imports
  - Update navigation links
  - Update sidebar menus

Commit 17: [DOCS] Update documentation files
  - README.md
  - QUICKSTART.md
  - DEPLOYMENT.md
  - docs/*.md

Commit 18: [CONFIG] Update environment templates
  - Update env_template.txt
  - Update env.production.template
  - Add deprecation notes for old variable names

Commit 19: [MIGRATION] Update migration files (app_label only)
  - Update existing migrations: app_label in Meta
  - Create data migration to update ContentType entries
  - Update permissions (content_type references)

Commit 20: [TEST] Update test fixtures and imports
  - Update pytest.ini
  - Update test imports
  - Update test data references

Commit 21: [VERIFY] Final verification and cleanup
  - Run full test suite
  - Verify backward compatibility redirects
  - Update CHANGELOG.md
```

### 2.3 Backward Compatibility Strategy

#### 2.3.1 Python Import Aliases

Create shadow modules that re-export from new locations:

```python
# careerbridge/__init__.py (DEPRECATED - remove after 6 months)
import warnings
warnings.warn(
    "The 'careerbridge' package is deprecated. Use 'gateai' instead.",
    DeprecationWarning,
    stacklevel=2
)
from gateai import *  # Re-export everything

# resumes/__init__.py (DEPRECATED)
from ats_signals import *
```

#### 2.3.2 URL Redirects (Django)

Add URL redirects in main `urls.py`:

```python
# Temporary redirects (maintain for 6 months)
from django.views.generic import RedirectView

urlpatterns += [
    path('api/v1/resumes/', RedirectView.as_view(url='/api/v1/ats-signals/', permanent=False)),
    path('api/v1/mentors/', RedirectView.as_view(url='/api/v1/human-loop/', permanent=False)),
    path('api/v1/appointments/', RedirectView.as_view(url='/api/v1/decision-slots/', permanent=False)),
    path('api/v1/notifications/', RedirectView.as_view(url='/api/v1/signal-delivery/', permanent=False)),
]
```

#### 2.3.3 Frontend Route Redirects (React Router)

Add redirect routes in `App.tsx`:

```typescript
<Route path="/resumes" element={<Navigate to="/ats-signals" replace />} />
<Route path="/mentors" element={<Navigate to="/human-loop" replace />} />
// ... etc
```

#### 2.3.4 Environment Variable Support

Support both old and new env vars during transition:

```python
# config.py
JOB_INGESTION_ENGINE_BASE_URL = os.getenv(
    'JOB_INGESTION_ENGINE_BASE_URL',
    os.getenv('JOB_CRAWLER_BASE_URL', 'http://localhost:8000')  # Fallback to old
)
```

### 2.4 Rollback Strategy

#### 2.4.1 Git-Based Rollback

- Each commit is atomic and reversible
- Use `git revert` for individual commits
- Tag each phase completion: `v1.0.0-gateai-phase-B`, etc.

#### 2.4.2 Database Rollback

- **No schema changes** - database names and tables remain unchanged
- ContentType migrations are reversible
- Permissions can be regenerated

#### 2.4.3 Deployment Rollback

- Keep previous Docker images tagged
- Quick rollback: `docker-compose -f docker-compose.prod.yml down && git checkout <previous-tag>`
- Environment variables can coexist during rollback

#### 2.4.4 Frontend Rollback

- Build artifacts are versioned
- Can deploy previous frontend build independently
- Route redirects ensure old URLs still work

---

## 3. Risk Assessment

### 3.1 High-Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Import path failures** | High - Runtime errors | Comprehensive import alias shims, extensive testing |
| **Django app_label in migrations** | Medium - Migration conflicts | Update app_label in migrations, test migration rollback |
| **Celery task discovery** | Medium - Task not found | Update CELERY_IMPORTS, verify task registration |
| **Frontend API calls breaking** | High - UI failures | Maintain API redirects, update API clients gradually |
| **Docker service name conflicts** | Medium - Deployment failures | Test docker-compose changes in staging |
| **Environment variable mismatches** | Low - Config errors | Support both old/new vars during transition |
| **ContentType foreign keys** | Medium - Permission/relation errors | Data migration to update ContentType entries |

### 3.2 Testing Strategy

#### 3.2.1 Unit Tests
- Update all test imports
- Verify model app_label changes
- Test import alias shims

#### 3.2.2 Integration Tests
- Test API redirects (old → new paths)
- Test Celery task execution
- Test external service connections

#### 3.2.3 E2E Tests
- Test frontend routing (old → new routes)
- Test user workflows (resume upload, mentor booking, etc.)
- Test backward compatibility URLs

#### 3.2.4 Migration Tests
- Test forward migrations
- Test rollback migrations
- Test ContentType updates

### 3.3 What Could Break

#### 3.3.1 Immediate Breakage (If Not Handled)
- ❌ Direct imports using old paths (mitigated by shims)
- ❌ Hardcoded API paths in frontend (mitigated by redirects)
- ❌ Celery task imports (mitigated by CELERY_IMPORTS update)
- ❌ Docker service discovery (mitigated by service name updates)

#### 3.3.2 Gradual Migration Issues
- ⚠️ Third-party integrations using old API paths (use redirects)
- ⚠️ Cached API responses in frontend (clear cache)
- ⚠️ Bookmarked URLs (redirects handle this)
- ⚠️ Email templates with old branding (update templates)

#### 3.3.3 Long-Term Considerations
- ⚠️ SEO impact from URL changes (301 redirects help)
- ⚠️ API documentation needs updates (Swagger metadata)
- ⚠️ Monitoring/alerting dashboards (update service names)

---

## 4. Implementation Checklist

### 4.1 Pre-Migration
- [ ] Create feature branch: `feature/gateai-identity-migration`
- [ ] Run full test suite (baseline)
- [ ] Document current API usage (for redirects)
- [ ] Backup database
- [ ] Tag current version: `v1.0.0-careerbridge-final`

### 4.2 During Migration (Per Commit)
- [ ] Make atomic changes
- [ ] Run tests after each commit
- [ ] Verify backward compatibility
- [ ] Update this checklist

### 4.3 Post-Migration
- [ ] Full test suite passes
- [ ] Manual testing of critical workflows
- [ ] Verify redirects work (old URLs → new URLs)
- [ ] Update deployment documentation
- [ ] Notify team of changes
- [ ] Monitor error logs for import/deprecation warnings
- [ ] Plan deprecation timeline for shims (6 months)

---

## 5. Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|---------------|--------------|
| Phase A (Planning) | ✅ Complete | - |
| Phase B (Backend Core) | 4-6 hours | Phase A |
| Phase C (Django Apps) | 8-12 hours | Phase B |
| Phase D (External Services) | 4-6 hours | Phase B |
| Phase E (Frontend) | 6-8 hours | Phase C |
| Phase F (Infrastructure) | 3-4 hours | Phase D |
| Phase G (Documentation) | 3-4 hours | All phases |
| Phase H (Cleanup) | 2-3 hours | All phases |
| **Total** | **30-43 hours** | |

**Recommended Approach**: Spread over 1-2 weeks with daily commits and testing.

---

## 6. Notes and Considerations

### 6.1 Database Considerations
- **No table renames** - Django migrations will handle app_label updates
- ContentType entries will be updated via data migration
- Foreign key constraints remain unchanged
- Database name can change (new deployments) but old DBs remain compatible

### 6.2 Third-Party Dependencies
- No changes to `requirements.txt` or `package.json`
- External API clients (Stripe, OpenAI) unaffected
- Email service templates need branding updates (separate task)

### 6.3 CI/CD Pipeline
- Update build scripts if they reference old paths
- Update deployment scripts (already in scope)
- Update monitoring/alerting service names

### 6.4 Documentation References
- External documentation sites (if any)
- API client libraries (if published)
- Developer onboarding materials

---

## 7. Success Criteria

✅ All tests pass  
✅ No breaking changes for existing API consumers (redirects work)  
✅ Frontend routes accessible via both old and new paths  
✅ Import shims work correctly  
✅ Docker services start successfully  
✅ Documentation updated and accurate  
✅ Zero production downtime during deployment  

---

## 8. Next Steps

1. **Review this plan** with team
2. **Get approval** to proceed to Phase B
3. **Create feature branch** and begin implementation
4. **Execute commits** in planned sequence
5. **Test thoroughly** after each phase
6. **Deploy to staging** for validation
7. **Deploy to production** with monitoring
8. **Plan deprecation** timeline for backward compatibility shims

---

**END OF PHASE A - PLANNING DOCUMENT**

*No code changes have been made. This is a planning document only.*

