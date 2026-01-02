# =========================
# 2) 重构：external_services/health_check.py
# =========================
# ✅ 移除所有 “from xxx import openai_service/email_service/job_crawler_service”
# ✅ 移除模块底部 health_checker = ExternalServicesHealthCheck()
# ✅ services 字典里放 getter（函数），运行期再取实例

import logging
from typing import Dict, List, Any
from datetime import datetime

from .config import config
from .registry import (
    get_openai_service,
    get_email_service,
    get_job_crawler_service,
)

logger = logging.getLogger(__name__)


class ExternalServicesHealthCheck:
    """Comprehensive health check for all external services"""

    def __init__(self):
        # 注意：这里放的是 getter，不是实例
        self.service_getters = {
            "openai": get_openai_service,
            "email": get_email_service,
            "job_crawler": get_job_crawler_service,
        }

    def check_all_services(self) -> Dict[str, Any]:
        health_results = {}
        overall_status = "healthy"

        for service_name, getter in self.service_getters.items():
            try:
                service_instance = getter()
                if service_instance is None:
                    health_results[service_name] = {
                        "status": "skipped",
                        "reason": "migration_mode_or_disabled",
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                health_result = service_instance.check_health()
                health_results[service_name] = health_result

                if health_result.get("status") == "unhealthy":
                    overall_status = "unhealthy"

            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_results[service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                overall_status = "unhealthy"

        config_status = self._validate_configurations()
        health_results["configuration"] = config_status
        if config_status.get("status") == "unhealthy":
            overall_status = "unhealthy"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": health_results,
            "summary": self._generate_summary(health_results),
        }

    def _validate_configurations(self) -> Dict[str, Any]:
        validation_results = config.validate_config()
        service_status = config.get_service_status()

        missing_configs = []
        configured_services = []

        for service, is_valid in validation_results.items():
            if is_valid:
                configured_services.append(service)
            else:
                missing_configs.append(service)

        if missing_configs:
            return {
                "status": "unhealthy",
                "configured_services": configured_services,
                "missing_configs": missing_configs,
                "message": f"Missing configurations for: {', '.join(missing_configs)}",
            }

        return {
            "status": "healthy",
            "configured_services": configured_services,
            "missing_configs": [],
            "message": "All services configured",
        }

    def _generate_summary(self, services_dict: Dict[str, Any]) -> Dict[str, Any]:
        # 这里 services_dict 是 check_all_services() 里的 health_results
        # 里面既有 openai/email/job_crawler，也有 configuration
        total = 0
        healthy = 0
        unhealthy = 0

        for _, result in services_dict.items():
            if not isinstance(result, dict):
                continue
            if "status" not in result:
                continue
            total += 1
            if result.get("status") == "healthy":
                healthy += 1
            elif result.get("status") == "unhealthy":
                unhealthy += 1

        return {
            "total_services": total,
            "healthy_services": healthy,
            "unhealthy_services": unhealthy,
            "health_percentage": (healthy / total * 100) if total > 0 else 0,
        }

    def check_specific_service(self, service_name: str) -> Dict[str, Any]:
        if service_name not in self.service_getters:
            return {
                "status": "unhealthy",
                "error": f"Unknown service: {service_name}",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            service_instance = self.service_getters[service_name]()
            if service_instance is None:
                return {
                    "status": "skipped",
                    "reason": "migration_mode_or_disabled",
                    "timestamp": datetime.now().isoformat(),
                }

            health_result = service_instance.check_health()
            health_result["timestamp"] = datetime.now().isoformat()
            return health_result

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
