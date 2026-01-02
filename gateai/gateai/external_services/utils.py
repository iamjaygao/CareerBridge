"""
External Services Utilities

Common utility functions for external service integrations including
error handling, retry mechanisms, logging, and response processing.
"""

import logging
import time
import json
from typing import Any, Dict, Optional, Callable
from functools import wraps
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from django.conf import settings


# Configure logging
logger = logging.getLogger(__name__)


class ExternalServiceError(Exception):
    """Base exception for external service errors"""
    def __init__(self, message: str, service: str, status_code: Optional[int] = None):
        self.message = message
        self.service = service
        self.status_code = status_code
        super().__init__(self.message)


class RateLimitError(ExternalServiceError):
    """Exception for rate limit exceeded"""
    pass


class AuthenticationError(ExternalServiceError):
    """Exception for authentication failures"""
    pass


class CircuitBreaker:
    """Simple circuit breaker for external services"""
    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at >= self.reset_timeout:
            return False
        return True

    def on_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time.time()


_service_breakers: Dict[str, CircuitBreaker] = {}
_service_metrics: Dict[str, Dict[str, Any]] = {}


def get_circuit_breaker(service: str) -> CircuitBreaker:
    if service not in _service_breakers:
        _service_breakers[service] = CircuitBreaker()
        _service_metrics[service] = {
            'success': 0,
            'timeout': 0,
            'conn_error': 0,
            'request_error': 0,
            'open_events': 0,
        }
    return _service_breakers[service]

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (RequestException, ExternalServiceError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise last_exception
                    
                    # Don't retry on authentication errors
                    if isinstance(e, AuthenticationError):
                        logger.error(f"Authentication error in {func.__name__}: {e}")
                        raise e
                    
                    # Don't retry on rate limit errors
                    if isinstance(e, RateLimitError):
                        logger.warning(f"Rate limit exceeded in {func.__name__}: {e}")
                        raise e
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator


def log_api_call(service: str, endpoint: str, method: str = "GET"):
    """
    Decorator to log API calls
    
    Args:
        service: Name of the external service
        endpoint: API endpoint being called
        method: HTTP method being used
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{service} {method} {endpoint} - Success ({duration:.2f}s)")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{service} {method} {endpoint} - Failed ({duration:.2f}s): {e}")
                raise
        
        return wrapper
    return decorator


def validate_response(response: requests.Response, service: str) -> Dict[str, Any]:
    """
    Validate and process API response
    
    Args:
        response: Requests response object
        service: Name of the service for error messages
    
    Returns:
        Parsed JSON response
    
    Raises:
        ExternalServiceError: If response is not valid
    """
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed for {service}", service, response.status_code)
        elif response.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded for {service}", service, response.status_code)
        else:
            raise ExternalServiceError(f"HTTP error for {service}: {e}", service, response.status_code)
    
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ExternalServiceError(f"Invalid JSON response from {service}: {e}", service)


def make_api_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    service: str = "Unknown"
) -> Dict[str, Any]:
    """
    Make HTTP request to external API with error handling
    
    Args:
        url: API endpoint URL
        method: HTTP method
        headers: Request headers
        data: Request data
        timeout: Request timeout in seconds
        service: Service name for logging
    
    Returns:
        Parsed JSON response
    
    Raises:
        ExternalServiceError: If request fails
    """
    breaker = get_circuit_breaker(service)

    if breaker.is_open():
        _service_metrics[service]['open_events'] += 1
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                scope.set_tag('service', service)
                scope.set_tag('circuit', 'open')
                sentry_sdk.capture_message(f"Circuit open for {service}")
        except Exception:
            pass
        raise ExternalServiceError(f"Circuit open for {service}", service)

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=timeout
        )
        result = validate_response(response, service)
        breaker.on_success()
        _service_metrics[service]['success'] += 1
        return result
    except Timeout:
        breaker.on_failure()
        _service_metrics[service]['timeout'] += 1
        raise ExternalServiceError(f"Timeout for {service} request", service)
    except ConnectionError:
        breaker.on_failure()
        _service_metrics[service]['conn_error'] += 1
        raise ExternalServiceError(f"Connection error for {service}", service)
    except RequestException as e:
        breaker.on_failure()
        _service_metrics[service]['request_error'] += 1
        raise ExternalServiceError(f"Request failed for {service}: {e}", service)


def get_service_metrics(service: Optional[str] = None) -> Dict[str, Any]:
    """Expose in-memory service metrics for debugging/health endpoints."""
    if service:
        return _service_metrics.get(service, {})
    return _service_metrics


def sanitize_api_key(api_key: str) -> str:
    """
    Sanitize API key for logging (show only first and last 4 characters)
    
    Args:
        api_key: Original API key
    
    Returns:
        Sanitized API key string
    """
    if not api_key or len(api_key) < 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error message for logging and user display
    
    Args:
        error: Exception object
        context: Additional context information
    
    Returns:
        Formatted error message
    """
    if isinstance(error, ExternalServiceError):
        base_message = f"{error.service}: {error.message}"
    else:
        base_message = str(error)
    
    if context:
        return f"{context} - {base_message}"
    return base_message


def check_service_health(service_name: str, health_check_func: Callable) -> Dict[str, Any]:
    """
    Check health status of external service
    
    Args:
        service_name: Name of the service
        health_check_func: Function to perform health check
    
    Returns:
        Health status dictionary
    """
    start_time = time.time()
    
    try:
        result = health_check_func()
        duration = time.time() - start_time
        
        return {
            "service": service_name,
            "status": "healthy",
            "response_time": duration,
            "timestamp": time.time(),
            "details": result
        }
    except Exception as e:
        duration = time.time() - start_time
        
        return {
            "service": service_name,
            "status": "unhealthy",
            "response_time": duration,
            "timestamp": time.time(),
            "error": str(e)
        }


def create_headers(api_key: str, content_type: str = "application/json") -> Dict[str, str]:
    """
    Create standard headers for API requests
    
    Args:
        api_key: API key for authentication
        content_type: Content type header
    
    Returns:
        Headers dictionary
    """
    headers = {
        "Content-Type": content_type,
        "User-Agent": "CareerBridge/1.0"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    return headers


def parse_pagination_params(page: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Parse pagination parameters for API requests
    
    Args:
        page: Page number
        page_size: Number of items per page
    
    Returns:
        Pagination parameters dictionary
    """
    params = {}
    
    if page is not None:
        params["page"] = page
    
    if page_size is not None:
        params["page_size"] = min(page_size, 100)  # Limit page size
    
    return params 
