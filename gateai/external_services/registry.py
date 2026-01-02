# =========================
# 0) 新增：external_services/registry.py
# =========================
# 位置建议：careerbridge/external_services/registry.py
# （如果你现在 external_services 是一个 app/包，就放在那个目录下）

from typing import Optional
from .migration_mode import is_migration_mode

# 这里用“函数内导入”，避免 import 链条过长带来副作用
_openai_service = None
_email_service = None
_job_crawler_service = None


def get_openai_service():
    global _openai_service
    if _openai_service is None:
        if is_migration_mode():
            # migration 阶段不要创建（保险）
            return None
        from .ai_services.openai_service import OpenAIService
        _openai_service = OpenAIService()
    return _openai_service


def get_email_service():
    global _email_service
    if _email_service is None:
        if is_migration_mode():
            return None
        from .third_party_apis.email_service import EmailService
        _email_service = EmailService()
    return _email_service


def get_job_crawler_service():
    global _job_crawler_service
    if _job_crawler_service is None:
        if is_migration_mode():
            return None
        from .third_party_apis.job_crawler import JobCrawlerService
        _job_crawler_service = JobCrawlerService()
    return _job_crawler_service
