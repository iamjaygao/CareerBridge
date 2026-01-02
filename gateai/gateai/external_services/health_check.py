"""
External Services Health Check

This module provides comprehensive health checking for all external services
including AI services, third-party APIs, and communication services.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from .config import config
from .ai_services.openai_service import openai_service
from .third_party_apis.email_service import email_service
from .third_party_apis.job_crawler import job_crawler_service
from .utils import check_service_health

logger = logging.getLogger(__name__)


class ExternalServicesHealthCheck:
    """Comprehensive health check for all external services"""
    
    def __init__(self):
        self.services = {
            "openai": openai_service,
            "email": email_service,
            "job_crawler": job_crawler_service
        }
    
    def check_all_services(self) -> Dict[str, Any]:
        """
        Check health of all external services
        
        Returns:
            Comprehensive health status for all services
        """
        health_results = {}
        overall_status = "healthy"
        
        for service_name, service_instance in self.services.items():
            try:
                health_result = service_instance.check_health()
                health_results[service_name] = health_result
                
                if health_result.get("status") == "unhealthy":
                    overall_status = "unhealthy"
                    
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_results[service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                overall_status = "unhealthy"
        
        # Add configuration validation
        config_status = self._validate_configurations()
        health_results["configuration"] = config_status
        
        if config_status.get("status") == "unhealthy":
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": health_results,
            "summary": self._generate_summary(health_results)
        }
    
    def _validate_configurations(self) -> Dict[str, Any]:
        """Validate all external service configurations"""
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
                "message": f"Missing configurations for: {', '.join(missing_configs)}"
            }
        else:
            return {
                "status": "healthy",
                "configured_services": configured_services,
                "missing_configs": [],
                "message": "All services configured"
            }
    
    def _generate_summary(self, health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of health check results"""
        total_services = len(health_results.get("services", {}))
        healthy_services = 0
        unhealthy_services = 0
        
        for service_name, result in health_results.get("services", {}).items():
            if result.get("status") == "healthy":
                healthy_services += 1
            else:
                unhealthy_services += 1
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0
        }
    
    def check_specific_service(self, service_name: str) -> Dict[str, Any]:
        """
        Check health of a specific service
        
        Args:
            service_name: Name of the service to check
        
        Returns:
            Health status of the specific service
        """
        if service_name not in self.services:
            return {
                "status": "unhealthy",
                "error": f"Unknown service: {service_name}",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            service_instance = self.services[service_name]
            health_result = service_instance.check_health()
            health_result["timestamp"] = datetime.now().isoformat()
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_status_report(self) -> Dict[str, Any]:
        """
        Get detailed status report for all services
        
        Returns:
            Detailed status report with configuration and health information
        """
        health_check = self.check_all_services()
        config_status = config.get_service_status()
        
        return {
            "health_check": health_check,
            "configuration_status": config_status,
            "recommendations": self._generate_recommendations(health_check, config_status),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_recommendations(
        self, 
        health_check: Dict[str, Any], 
        config_status: Dict[str, str]
    ) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Check for missing configurations
        for service, status in config_status.items():
            if status == "not_configured":
                recommendations.append(f"Configure {service} API key in environment variables")
        
        # Check for unhealthy services
        for service_name, result in health_check.get("services", {}).items():
            if result.get("status") == "unhealthy":
                error = result.get("error", "Unknown error")
                recommendations.append(f"Investigate {service_name} service: {error}")
        
        # Check overall health
        if health_check.get("overall_status") == "unhealthy":
            recommendations.append("Review external service configurations and connections")
        
        if not recommendations:
            recommendations.append("All external services are healthy and properly configured")
        
        return recommendations


# Global health check instance
health_checker = ExternalServicesHealthCheck() 