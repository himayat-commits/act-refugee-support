"""
Comprehensive Error Handling and Logging System
Provides centralized error management, logging, and monitoring
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Categories of errors for better tracking"""

    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class CustomLogger:
    """Enhanced logger with structured logging and multiple outputs"""

    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level))

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File Handler - General logs
        file_handler = logging.FileHandler(LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

        # Error File Handler - Errors only
        error_handler = logging.FileHandler(LOGS_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        self.logger.addHandler(error_handler)

        # JSON File Handler - Structured logs for analysis
        self.json_handler = JsonFileHandler(LOGS_DIR / f"structured_{name}_{datetime.now().strftime('%Y%m%d')}.json")
        self.logger.addHandler(self.json_handler)

    def log_structured(self, level: LogLevel, message: str, **kwargs):
        """Log with structured data for better analysis"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "metadata": kwargs,
        }

        # Log to standard logger
        log_func = getattr(self.logger, level.value.lower())
        log_func(f"{message} | {json.dumps(kwargs)}")

        # Also write to JSON file
        self.json_handler.emit_json(log_data)

        return log_data

    def log_error(self, error: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR, **context):
        """Log error with full context and traceback"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category.value,
            "traceback": traceback.format_exc(),
            "context": context,
        }

        self.log_structured(LogLevel.ERROR, f"Error occurred: {error}", **error_data)
        return error_data

    def log_api_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log API request details"""
        self.log_structured(
            LogLevel.INFO,
            f"API Request: {method} {path}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_search_query(self, query: str, results_count: int, duration_ms: float, **kwargs):
        """Log search query details"""
        self.log_structured(
            LogLevel.INFO,
            f"Search Query: '{query}'",
            query=query,
            results_count=results_count,
            duration_ms=duration_ms,
            **kwargs,
        )


class JsonFileHandler(logging.Handler):
    """Custom handler for JSON structured logging"""

    def __init__(self, filename: Path):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        """Standard emit method for logging handler"""

    def emit_json(self, log_data: Dict):
        """Write JSON log entry"""
        try:
            with open(self.filename, "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception as e:
            print(f"Failed to write JSON log: {e}")


class ErrorHandler:
    """Centralized error handling system"""

    def __init__(self, logger: CustomLogger):
        self.logger = logger
        self.error_counts = {}
        self.error_threshold = 10  # Alert after 10 errors of same type

    def handle_error(self, error: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR, **context) -> Dict:
        """Handle error with logging and potential recovery"""

        # Log the error
        error_data = self.logger.log_error(error, category, **context)

        # Track error counts
        error_key = f"{category.value}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Check if we need to alert
        if self.error_counts[error_key] >= self.error_threshold:
            self.send_alert(error_key, error_data)

        # Attempt recovery based on error type
        recovery_action = self.attempt_recovery(error, category)

        return {
            "error": error_data,
            "recovery_attempted": recovery_action is not None,
            "recovery_action": recovery_action,
        }

    def attempt_recovery(self, error: Exception, category: ErrorCategory) -> Optional[str]:
        """Attempt to recover from specific error types"""

        if category == ErrorCategory.DATABASE_ERROR:
            # Try to reconnect to database
            return "database_reconnect"

        elif category == ErrorCategory.EXTERNAL_SERVICE_ERROR:
            # Could implement retry logic
            return "service_retry"

        elif category == ErrorCategory.RATE_LIMIT_ERROR:
            # Implement backoff
            return "rate_limit_backoff"

        return None

    def send_alert(self, error_key: str, error_data: Dict):
        """Send alert for critical errors"""
        self.logger.log_structured(
            LogLevel.CRITICAL,
            f"ALERT: Error threshold reached for {error_key}",
            error_key=error_key,
            count=self.error_counts[error_key],
            latest_error=error_data,
        )
        # TODO: Implement actual alerting (email, Slack, etc.)


def error_handler_decorator(category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR):
    """Decorator for automatic error handling"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = CustomLogger(func.__module__)
                handler = ErrorHandler(logger)
                error_info = handler.handle_error(
                    e, category, function=func.__name__, args=str(args)[:100], kwargs=str(kwargs)[:100]
                )
                raise  # Re-raise after logging

        return wrapper

    return decorator


def async_error_handler_decorator(category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR):
    """Decorator for async functions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger = CustomLogger(func.__module__)
                handler = ErrorHandler(logger)
                error_info = handler.handle_error(
                    e, category, function=func.__name__, args=str(args)[:100], kwargs=str(kwargs)[:100]
                )
                raise  # Re-raise after logging

        return wrapper

    return decorator


class APIErrorResponse:
    """Standardized API error responses"""

    @staticmethod
    def create(
        status_code: int,
        error_type: str,
        message: str,
        details: Optional[Dict] = None,
        request_id: Optional[str] = None,
    ) -> Dict:
        """Create standardized error response"""
        return {
            "error": {
                "status_code": status_code,
                "type": error_type,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
            }
        }

    @staticmethod
    def validation_error(errors: Dict) -> Dict:
        """Create validation error response"""
        return APIErrorResponse.create(
            status_code=422,
            error_type="validation_error",
            message="Validation failed",
            details={"validation_errors": errors},
        )

    @staticmethod
    def not_found(resource: str) -> Dict:
        """Create not found error response"""
        return APIErrorResponse.create(
            status_code=404, error_type="not_found", message=f"{resource} not found", details={"resource": resource}
        )

    @staticmethod
    def internal_error(request_id: str) -> Dict:
        """Create internal server error response"""
        return APIErrorResponse.create(
            status_code=500,
            error_type="internal_error",
            message="An internal error occurred. Please try again later.",
            request_id=request_id,
        )

    @staticmethod
    def rate_limit_exceeded(retry_after: int) -> Dict:
        """Create rate limit error response"""
        return APIErrorResponse.create(
            status_code=429,
            error_type="rate_limit_exceeded",
            message="Rate limit exceeded. Please try again later.",
            details={"retry_after_seconds": retry_after},
        )


class PerformanceMonitor:
    """Monitor performance and log slow operations"""

    def __init__(self, logger: CustomLogger):
        self.logger = logger
        self.slow_query_threshold_ms = 1000  # 1 second
        self.slow_api_threshold_ms = 2000  # 2 seconds

    def log_slow_operation(self, operation_type: str, duration_ms: float, **context):
        """Log slow operations for analysis"""
        self.logger.log_structured(
            LogLevel.WARNING,
            f"Slow {operation_type} detected: {duration_ms}ms",
            operation_type=operation_type,
            duration_ms=duration_ms,
            **context,
        )

    def check_query_performance(self, query: str, duration_ms: float):
        """Check and log slow database queries"""
        if duration_ms > self.slow_query_threshold_ms:
            self.log_slow_operation("query", duration_ms, query=query)

    def check_api_performance(self, endpoint: str, duration_ms: float):
        """Check and log slow API responses"""
        if duration_ms > self.slow_api_threshold_ms:
            self.log_slow_operation("api_call", duration_ms, endpoint=endpoint)


# Global logger instance
main_logger = CustomLogger("refugee_support")
error_handler = ErrorHandler(main_logger)
performance_monitor = PerformanceMonitor(main_logger)


# Example usage functions
def log_info(message: str, **kwargs):
    """Convenience function for info logging"""
    main_logger.log_structured(LogLevel.INFO, message, **kwargs)


def log_error(error: Exception, **kwargs):
    """Convenience function for error logging"""
    error_handler.handle_error(error, **kwargs)


def log_warning(message: str, **kwargs):
    """Convenience function for warning logging"""
    main_logger.log_structured(LogLevel.WARNING, message, **kwargs)


def log_debug(message: str, **kwargs):
    """Convenience function for debug logging"""
    main_logger.log_structured(LogLevel.DEBUG, message, **kwargs)
