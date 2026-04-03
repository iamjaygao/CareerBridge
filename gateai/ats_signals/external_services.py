"""
resumes/external_services.py

External service clients used by the resumes app.

Goals of this refactor:
- ✅ No DB queries at import-time (so `makemigrations/migrate` won't crash)
- ✅ Safe behavior when the ExternalServiceIntegration table doesn't exist yet
- ✅ Lazy-loading of service configs + clients
- ✅ Clean, consistent request logging + error handling
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any

import os
import time
import json
import logging

import httpx
from django.utils import timezone
from django.db.utils import OperationalError, ProgrammingError

from .models import (
    ExternalServiceIntegration,
    ServiceUsageLog,
    JobDescription,
    ResumeJobMatch,
    Resume,
)

logger = logging.getLogger(__name__)


def is_migration_mode() -> bool:
    """
    When running migrations, Django imports a lot of modules before tables exist.
    Set:
        export DJANGO_MIGRATION_MODE=1
    to skip all external-service DB reads.
    """
    return os.environ.get("DJANGO_MIGRATION_MODE") == "1"


class ExternalServiceClient:
    """Base client for external service integration (DB-configured)."""

    def __init__(self, service_type: str):
        self.service_type = service_type
        self._service_config: Optional[ExternalServiceIntegration] = None
        self._service_config_loaded: bool = False  # distinguish "not loaded" vs "loaded but missing"

    def get_service_config(self) -> Optional[ExternalServiceIntegration]:
        """
        Lazy-load the active service config from DB.

        IMPORTANT:
        - Never crash migrations if table doesn't exist yet.
        - Never query DB in migration mode.
        """
        if is_migration_mode():
            return None

        if self._service_config_loaded:
            return self._service_config

        self._service_config_loaded = True
        try:
            self._service_config = ExternalServiceIntegration.objects.get(
                service_type=self.service_type, is_active=True
            )
        except ExternalServiceIntegration.DoesNotExist:
            self._service_config = None
        except (OperationalError, ProgrammingError) as e:
            # DB not ready (migrations in progress) — don't blow up
            logger.debug("DB not ready when loading service config %s: %s", self.service_type, e)
            self._service_config = None

        return self._service_config

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        user=None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request via centralized utils (retry/circuit etc).
        """
        service_config = self.get_service_config()
        if not service_config:
            raise RuntimeError(f"No active service configuration for '{self.service_type}'")

        from external_services.utils import make_api_request, ExternalServiceError

        url = f"{service_config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "CareerBridge/1.0",
        }

        # auth_headers might be JSONField/dict in your model
        if service_config.auth_headers:
            try:
                headers.update(service_config.auth_headers if isinstance(service_config.auth_headers, dict) else json.loads(service_config.auth_headers))
            except Exception:
                logger.debug("Failed to parse auth_headers for %s", self.service_type)

        if service_config.api_key:
            headers["Authorization"] = f"Bearer {service_config.api_key}"

        start_time = time.time()
        try:
            resp = make_api_request(url, method=method, headers=headers, json=data, timeout=service_config.timeout or 10)
            duration = time.time() - start_time
            self._log_request(
                service_config=service_config,
                endpoint=endpoint,
                method=method,
                request_data=data or {},
                response_status=resp.get("status_code", 200),
                response_data=resp.get("body", resp),
                request_time=duration,
                is_success=True,
                user=user,
            )
            return resp.get("body", resp) if isinstance(resp, dict) else resp
        except ExternalServiceError as e:
            duration = time.time() - start_time
            self._log_request(
                service_config=service_config,
                endpoint=endpoint,
                method=method,
                request_data=data or {},
                response_status=getattr(e, "status_code", 500),
                response_data={"error": str(e)},
                request_time=duration,
                is_success=False,
                user=user,
                error_message=str(e),
            )
            raise

    def _log_request(
        self,
        *,
        service_config: ExternalServiceIntegration,
        endpoint: str,
        method: str,
        request_data: Dict[str, Any],
        response_status: int,
        response_data: Dict[str, Any],
        request_time: float,
        is_success: bool,
        user=None,
        error_message: str = "",
    ) -> None:
        """
        Log service request.
        Never crash the main flow if logging fails.
        """
        # During migrations / early boot, tables may not exist yet
        if is_migration_mode():
            return

        try:
            # Best-effort logging; schema may differ between projects.
            # Wrap in try/except so logging never breaks main flow.
            ServiceUsageLog.objects.create(
                service=service_config,
                endpoint=endpoint[:255],
                method=method,
                request_data=json.dumps(request_data) if request_data is not None else "",
                response_status=response_status,
                response_data=json.dumps(response_data) if response_data is not None else "",
                duration=request_time,
                success=bool(is_success),
                user_id=str(user.id) if user and hasattr(user, "id") else None,
                error_message=error_message,
                timestamp=timezone.now(),
            )
        except (OperationalError, ProgrammingError) as e:
            logger.debug("DB not ready for service usage log: %s", e)
        except Exception:
            # Swallow any logging errors
            logger.exception("Failed to write ServiceUsageLog")


class JobCrawlerServiceClient(ExternalServiceClient):
    """Client for job crawler service (DB-configured)."""

    def __init__(self):
        super().__init__("job_crawler")

    def crawl_jobs(
        self,
        job_title: str,
        location: str,
        sources: Optional[List[str]] = None,
        limit: int = 20,
        user=None,
    ) -> List[Dict[str, Any]]:
        data = {
            "job_title": job_title,
            "location": location,
            "sources": sources or ["indeed", "linkedin"],
            "limit": limit,
        }
        response = self._make_request("crawl", method="POST", data=data, user=user)
        return response.get("jobs", []) if isinstance(response, dict) else []

    def get_job_details(self, job_id: str, user=None) -> Dict[str, Any]:
        return self._make_request(f"jobs/{job_id}", user=user)

    def search_jobs(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        user=None,
    ) -> Dict[str, Any]:
        data = {
            "query": query,
            "filters": filters or {},
            "page": page,
        }
        return self._make_request("search", method="POST", data=data, user=user)

    def check_health(self) -> Dict[str, Any]:
        try:
            resp = self._make_request("health", method="GET")
            return {"ok": True, "info": resp}
        except Exception as e:
            logger.debug("JobCrawler health check failed: %s", e)
            return {"ok": False, "error": str(e)}


class ResumeMatcherServiceClient:
    """
    Client for resume matching service (ENV-configured via careerbridge.external_services.config).

    NOTE:
    - This one does NOT use DB tables.
    - Still should not explode in migration mode.
    """

    def __init__(self):
        from external_services.config import config

        self.base_url = config.resume_matcher.base_url.rstrip("/")
        self.api_key = config.resume_matcher.api_key
        self.timeout = config.resume_matcher.timeout

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        user=None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "CareerBridge/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.request(method, url, json=data, headers=headers)
            try:
                body = resp.json()
            except Exception:
                body = {"text": resp.text}
            if resp.status_code >= 400:
                raise RuntimeError(f"Matcher request failed: {resp.status_code} {body}")
            return body

    def match_resume_to_jd(
        self,
        resume_text: str,
        job_description: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        user=None,
    ) -> Dict[str, Any]:
        data = {
            "resume_text": resume_text,
            "job_description": job_description,
            "job_title": job_title,
            "company": company,
            "user_id": str(user.id) if user else None,
        }
        return self._make_request("match", method="POST", data=data, user=user)

    def batch_match_resumes(
        self,
        resumes: List[Dict[str, Any]],
        job_descriptions: List[Dict[str, Any]],
        user=None,
    ) -> List[Dict[str, Any]]:
        data = {
            "resumes": resumes,
            "job_descriptions": job_descriptions,
            "user_id": str(user.id) if user else None,
        }
        resp = self._make_request("batch-match", method="POST", data=data, user=user)
        return resp.get("matches", [])

    def get_match_analysis(self, match_id: str, user=None) -> Dict[str, Any]:
        return self._make_request(f"matches/{match_id}/analysis", user=user)

    def provide_feedback(
        self,
        match_id: str,
        feedback: str,
        rating: int,
        user=None,
    ) -> Dict[str, Any]:
        data = {
            "feedback_text": feedback,
            "rating": rating,
            "user_id": str(user.id) if user else None,
        }
        return self._make_request(f"matches/{match_id}/feedback", method="POST", data=data, user=user)

    def check_health(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/health")
                return {"ok": resp.status_code == 200, "status_code": resp.status_code}
        except Exception as e:
            logger.debug("ResumeMatcher health check failed: %s", e)
            return {"ok": False, "error": str(e)}


class AIAnalysisServiceClient(ExternalServiceClient):
    """Client for AI analysis service (DB-configured)."""

    def __init__(self):
        super().__init__("ai_analyzer")

    def analyze_resume(
        self,
        resume_text: str,
        industry: Optional[str] = None,
        job_title: Optional[str] = None,
        user=None,
    ) -> Dict[str, Any]:
        data = {
            "resume_text": resume_text,
            "industry": industry,
            "job_title": job_title,
        }
        return self._make_request("analyze", method="POST", data=data, user=user)

    def get_analysis_feedback(self, analysis_id: str, user=None) -> Dict[str, Any]:
        return self._make_request(f"analysis/{analysis_id}/feedback", user=user)

    def compare_resumes(
        self,
        resume1_text: str,
        resume2_text: str,
        comparison_type: str = "version",
        user=None,
    ) -> Dict[str, Any]:
        data = {
            "resume1_text": resume1_text,
            "resume2_text": resume2_text,
            "comparison_type": comparison_type,
        }
        return self._make_request("compare", method="POST", data=data, user=user)


class ExternalServiceManager:
    """
    Manager for external service operations.

    IMPORTANT:
    - No external clients created at import-time.
    - Everything is lazy via @property.
    """

    def __init__(self):
        self._job_crawler: Optional[JobCrawlerServiceClient] = None
        self._resume_matcher: Optional[ResumeMatcherServiceClient] = None
        self._ai_analyzer: Optional[AIAnalysisServiceClient] = None

    @property
    def job_crawler(self) -> JobCrawlerServiceClient:
        if self._job_crawler is None:
            self._job_crawler = JobCrawlerServiceClient()
        return self._job_crawler

    @property
    def resume_matcher(self) -> ResumeMatcherServiceClient:
        if self._resume_matcher is None:
            self._resume_matcher = ResumeMatcherServiceClient()
        return self._resume_matcher

    @property
    def ai_analyzer(self) -> AIAnalysisServiceClient:
        if self._ai_analyzer is None:
            self._ai_analyzer = AIAnalysisServiceClient()
        return self._ai_analyzer

    def crawl_and_store_jobs(
        self,
        job_title: str,
        location: str,
        sources: Optional[List[str]] = None,
        limit: int = 20,
        user=None,
    ) -> List[JobDescription]:
        jobs = []
        try:
            jobs = self.job_crawler.crawl_jobs(job_title, location, sources=sources, limit=limit, user=user)
        except Exception as e:
            logger.debug("crawl_jobs failed: %s", e)
            return []

        created: List[JobDescription] = []
        for j in jobs:
            try:
                external_id = j.get("id") or j.get("external_id") or j.get("job_id")
                defaults = {
                    "title": j.get("title") or j.get("job_title"),
                    "company": j.get("company"),
                    "location": j.get("location"),
                    "description": j.get("description") or j.get("summary"),
                    "raw_payload": json.dumps(j),
                }
                if external_id:
                    obj, _ = JobDescription.objects.update_or_create(
                        external_id=str(external_id),
                        defaults=defaults,
                    )
                else:
                    obj = JobDescription.objects.create(**{k: v for k, v in defaults.items() if v is not None})
                created.append(obj)
            except Exception:
                logger.exception("Failed to store job from external crawler")
        return created

    def match_resume_to_external_jd(
        self,
        resume: Resume,
        job_description: JobDescription,
        user=None,
    ) -> Optional[ResumeJobMatch]:
        try:
            resume_text = getattr(resume, "full_text", None) or getattr(resume, "text", None) or str(resume)
            jd_text = getattr(job_description, "description", None) or getattr(job_description, "raw_payload", "")
            result = self.resume_matcher.match_resume_to_jd(resume_text, jd_text, job_title=job_description.title, company=job_description.company, user=user)
            # Best-effort persistence of match
            try:
                match, _ = ResumeJobMatch.objects.update_or_create(
                    external_match_id=result.get("match_id") if isinstance(result, dict) else None,
                    defaults={
                        "resume": resume,
                        "job_description": job_description,
                        "score": result.get("score") if isinstance(result, dict) else None,
                        "payload": json.dumps(result) if result is not None else None,
                    },
                )
                return match
            except Exception:
                logger.debug("Failed to persist ResumeJobMatch; returning raw result")
                return None
        except Exception:
            logger.exception("External match failed")
            return None

    def analyze_resume_externally(
        self,
        resume: Resume,
        industry: Optional[str] = None,
        job_title: Optional[str] = None,
        user=None,
    ):
        try:
            resume_text = getattr(resume, "full_text", None) or getattr(resume, "text", None) or str(resume)
            return self.ai_analyzer.analyze_resume(resume_text, industry=industry, job_title=job_title, user=user)
        except Exception:
            logger.exception("External resume analysis failed")
            return None

    def check_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        try:
            results["job_crawler"] = self.job_crawler.check_health()
        except Exception as e:
            results["job_crawler"] = {"ok": False, "error": str(e)}
        try:
            results["resume_matcher"] = self.resume_matcher.check_health()
        except Exception as e:
            results["resume_matcher"] = {"ok": False, "error": str(e)}
        try:
            results["ai_analyzer"] = self.ai_analyzer.check_health()
        except Exception as e:
            results["ai_analyzer"] = {"ok": False, "error": str(e)}
        return results


# --- runtime factories (no DB access at import-time) ---
_external_service_manager: Optional[ExternalServiceManager] = None

def get_external_service_manager() -> ExternalServiceManager:
    """
    Return a lazily-created ExternalServiceManager singleton.
    Avoids creating clients / touching the database at import time.
    """
    global _external_service_manager
    if _external_service_manager is None:
        _external_service_manager = ExternalServiceManager()
    return _external_service_manager

def get_job_crawler_service() -> JobCrawlerServiceClient:
    return get_external_service_manager().job_crawler

def get_resume_matcher_service() -> ResumeMatcherServiceClient:
    return get_external_service_manager().resume_matcher

def get_ai_analyzer_service() -> AIAnalysisServiceClient:
    return get_external_service_manager().ai_analyzer

# IMPORTANT:
# - No global instances here. Create them in runtime code (views/tasks) when needed.
#   Example:
#       manager = ExternalServiceManager()
#       manager.job_crawler.search_jobs(...)
