# =========================
# 3) 重构：ai_services/openai_service.py（lazy import + lazy client）
# =========================
# ✅ 不要在模块顶部 import openai/OpenAI（避免 SDK 未安装时直接崩）
# ✅ 不要在 __init__ 里初始化 client（按需 _get_client）
# ✅ check_health 也要优雅降级

import logging
import json
from typing import Dict, List, Any, Optional

from ..config import config
from ..utils import (
    retry_on_failure,
    log_api_call,
    ExternalServiceError,
    RateLimitError,
    AuthenticationError,
    sanitize_api_key,
)

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI API service integration"""

    def __init__(self):
        self._client = None
        self._init_error = None  # 记录初始化失败原因（不会在 import 阶段抛）

    def _lazy_import_openai(self):
        try:
            from openai import OpenAI  # noqa
            return OpenAI
        except Exception as e:
            raise ExternalServiceError(f"OpenAI SDK import failed: {e}", "openai")

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not config.openai.api_key:
            raise ExternalServiceError("OpenAI API key not configured", "openai")

        try:
            OpenAI = self._lazy_import_openai()
            self._client = OpenAI(api_key=config.openai.api_key)
            logger.info(
                f"OpenAI client initialized with key: {sanitize_api_key(config.openai.api_key)}"
            )
            return self._client
        except Exception as e:
            self._init_error = str(e)
            raise ExternalServiceError(f"OpenAI client initialization failed: {e}", "openai")

    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("OpenAI", "chat/completions", "POST")
    def analyze_resume(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        client = self._get_client()

        prompt = (
            self._create_targeted_analysis_prompt(resume_text, job_description)
            if job_description
            else self._create_general_analysis_prompt(resume_text)
        )

        try:
            response = client.chat.completions.create(
                model=config.openai.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume analyst and career advisor."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=config.openai.max_tokens,
                temperature=config.openai.temperature,
            )
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text)
        except Exception as e:
            error_text = str(e).lower()
            if "rate" in error_text or "429" in error_text:
                logger.warning("OpenAI rate limit encountered")
                raise RateLimitError("OpenAI rate limit exceeded", "openai")
            if "auth" in error_text or "key" in error_text or "401" in error_text:
                logger.error("OpenAI authentication failed")
                raise AuthenticationError("OpenAI authentication failed", "openai")
            logger.error(f"OpenAI resume analysis failed: {e}")
            raise ExternalServiceError(f"Resume analysis failed: {e}", "openai")

    def _create_general_analysis_prompt(self, resume_text: str) -> str:
        return f"""Please analyze the following resume and provide a comprehensive assessment in JSON format.

Resume:
{resume_text}

Return JSON with fields like overall_score, strengths, weaknesses, suggestions...
"""

    def _create_targeted_analysis_prompt(self, resume_text: str, job_description: str) -> str:
        return f"""Please analyze the resume against the job description and return JSON.

Resume:
{resume_text}

Job Description:
{job_description}
"""

    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, Any]:
        try:
            if "{" in analysis_text and "}" in analysis_text:
                start = analysis_text.find("{")
                end = analysis_text.rfind("}") + 1
                return json.loads(analysis_text[start:end])
            return {"analysis": analysis_text, "parsed": False}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse OpenAI response as JSON: {e}")
            return {"analysis": analysis_text, "parsed": False, "error": "Failed to parse structured response"}

    def check_health(self) -> Dict[str, Any]:
        try:
            if not config.openai.api_key:
                return {"status": "unhealthy", "error": "API key not configured"}

            client = self._get_client()
            client.chat.completions.create(
                model=config.openai.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                temperature=0,
            )
            return {"status": "healthy", "model": config.openai.model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
