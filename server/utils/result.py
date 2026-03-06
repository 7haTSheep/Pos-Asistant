"""
Result Pattern Implementation

Provides a type-safe way to handle success/failure results without exceptions.
Inspired by functional programming patterns and the Result<T> type from Rust/F#.

Usage:
    from utils.result import Result, Success, Failure, ErrorCode
    
    def some_operation() -> Result[int, str]:
        try:
            value = do_something()
            return Success(value)
        except SomeError as e:
            return Failure("Operation failed", ErrorCode.INVALID_BATCH)
    
    # Handle result
    result = some_operation()
    if result.is_success:
        print(f"Success: {result.value}")
    else:
        print(f"Error {result.error_code}: {result.error}")
"""

from __future__ import annotations
from typing import Generic, TypeVar, Optional, Union, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import json


# Type variables for generic Result
T = TypeVar('T')  # Success type
E = TypeVar('E', bound=str)  # Error type (must be string or subclass)


class ErrorCode(Enum):
    """
    Standard error codes for the application.
    Each error code has a machine-readable code and HTTP status mapping.
    """
    
    # Success (200s)
    SUCCESS = ("OK", 200)
    CREATED = ("CREATED", 201)
    
    # Inventory Errors (400s)
    INSUFFICIENT_STOCK = ("INV-001", 400)
    CAPACITY_EXCEEDED = ("INV-002", 400)
    INVALID_BATCH = ("INV-003", 400)
    INVALID_QUANTITY = ("INV-004", 400)
    INVALID_SLOT = ("INV-005", 400)
    CONCURRENT_MODIFICATION = ("INV-009", 400)
    RESERVATION_FAILED = ("INV-010", 400)
    
    # Not Found Errors (404s)
    NOT_FOUND = ("NOT-001", 404)
    USER_NOT_FOUND = ("NOT-002", 404)
    WAREHOUSE_NOT_FOUND = ("NOT-003", 404)
    ITEM_NOT_FOUND = ("INV-008", 404)
    BATCH_NOT_FOUND = ("INV-006", 404)
    SLOT_NOT_FOUND = ("INV-007", 404)
    
    # Authorization Errors (403s)
    UNAUTHORIZED = ("AUTH-001", 401)
    INSUFFICIENT_ROLE = ("AUTH-002", 403)
    INVALID_CREDENTIALS = ("AUTH-003", 401)
    TOKEN_EXPIRED = ("AUTH-004", 401)
    
    # Validation Errors (422s)
    VALIDATION_ERROR = ("VAL-001", 422)
    INVALID_INPUT = ("VAL-002", 422)
    
    # Server Errors (500s)
    DATABASE_ERROR = ("SRV-001", 500)
    INTERNAL_ERROR = ("SRV-002", 500)
    EXTERNAL_SERVICE_ERROR = ("SRV-003", 500)
    
    def __init__(self, code: str, http_status: int):
        self.code = code
        self.http_status = http_status
    
    def __str__(self) -> str:
        return self.code
    
    @classmethod
    def from_string(cls, code: str) -> ErrorCode:
        """Get ErrorCode from string code."""
        for error in cls:
            if error.code == code:
                return error
        return cls.INTERNAL_ERROR


@dataclass(frozen=True)
class Success(Generic[T]):
    """
    Represents a successful operation result.
    
    Attributes:
        value: The successful result value
        message: Optional success message
        metadata: Optional additional metadata
    """
    value: T
    message: str = field(default="Operation completed successfully")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        return True
    
    @property
    def is_failure(self) -> bool:
        return False
    
    @property
    def error(self) -> None:
        return None
    
    @property
    def error_code(self) -> None:
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_success": True,
            "value": self.value,
            "message": self.message,
            "metadata": self.metadata
        }
    
    def __bool__(self) -> bool:
        return True


@dataclass(frozen=True)
class Failure(Generic[E]):
    """
    Represents a failed operation result.
    
    Attributes:
        error: The error message
        error_code: Machine-readable error code
        details: Optional additional error details
    """
    error: E
    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        return False
    
    @property
    def is_failure(self) -> bool:
        return True
    
    @property
    def value(self) -> None:
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_success": False,
            "error": self.error,
            "error_code": self.error_code.code if self.error_code else None,
            "http_status": self.error_code.http_status if self.error_code else 500,
            "details": self.details
        }
    
    def __bool__(self) -> bool:
        return False


# Type alias for Result
Result = Union[Success[T], Failure[E]]


# ============================================================================
# Helper Functions
# ============================================================================

def success(value: T, message: str = "", metadata: Optional[Dict[str, Any]] = None) -> Success[T]:
    """
    Create a successful result.
    
    Args:
        value: The success value
        message: Optional success message
        metadata: Optional additional metadata
    
    Returns:
        Success[T] instance
    """
    return Success(
        value=value,
        message=message or "Operation completed successfully",
        metadata=metadata or {}
    )


def failure(error: E, error_code: ErrorCode = ErrorCode.INTERNAL_ERROR, 
            details: Optional[Dict[str, Any]] = None) -> Failure[E]:
    """
    Create a failure result.
    
    Args:
        error: The error message
        error_code: Machine-readable error code
        details: Optional additional error details
    
    Returns:
        Failure[E] instance
    """
    return Failure(
        error=error,
        error_code=error_code,
        details=details or {}
    )


# ============================================================================
# Result Extensions
# ============================================================================

class ResultExtensions:
    """Extension methods for Result types."""
    
    @staticmethod
    def map(result: Result[T, E], func) -> Result[Any, E]:
        """
        Transform the success value of a result.
        
        Args:
            result: The result to transform
            func: Function to apply to success value
        
        Returns:
            New Result with transformed value
        """
        if result.is_success:
            return Success(func(result.value))
        return result
    
    @staticmethod
    def bind(result: Result[T, E], func) -> Result[Any, E]:
        """
        Chain result-returning function.
        
        Args:
            result: The result to chain from
            func: Function that returns Result
        
        Returns:
            Result from the function
        """
        if result.is_success:
            return func(result.value)
        return result
    
    @staticmethod
    def unwrap(result: Result[T, E], default: Optional[T] = None) -> Optional[T]:
        """
        Get the value from a result, or default if failure.
        
        Args:
            result: The result to unwrap
            default: Default value if failure
        
        Returns:
            Success value or default
        """
        if result.is_success:
            return result.value
        return default
    
    @staticmethod
    def unwrap_or_raise(result: Result[T, E], exception: Exception = None) -> T:
        """
        Get the value or raise an exception on failure.
        
        Args:
            result: The result to unwrap
            exception: Exception to raise (default: ValueError)
        
        Returns:
            Success value
        
        Raises:
            Exception if result is failure
        """
        if result.is_success:
            return result.value
        
        exc = exception or ValueError(result.error)
        raise exc
    
    @staticmethod
    def combine(results: List[Result[T, E]]) -> Result[List[T], E]:
        """
        Combine multiple results into a single result.
        
        Args:
            results: List of results to combine
        
        Returns:
            Success with list of values, or first failure
        """
        values = []
        for result in results:
            if result.is_failure:
                return result
            values.append(result.value)
        return Success(values)


# ============================================================================
# HTTP Response Helpers
# ============================================================================

def result_to_http_response(result: Result[T, E]) -> tuple[Dict[str, Any], int]:
    """
    Convert a Result to HTTP response tuple (body, status_code).
    
    Args:
        result: The result to convert
    
    Returns:
        Tuple of (response_body, http_status_code)
    """
    if result.is_success:
        return result.to_dict(), result.error_code.http_status if result.error_code else 200
    else:
        return result.to_dict(), result.error_code.http_status


# ============================================================================
# JSON Serialization
# ============================================================================

class ResultEncoder(json.JSONEncoder):
    """Custom JSON encoder for Result types."""
    
    def default(self, obj):
        if isinstance(obj, (Success, Failure)):
            return obj.to_dict()
        if isinstance(obj, ErrorCode):
            return obj.code
        return super().default(obj)


def result_to_json(result: Result[T, E], **kwargs) -> str:
    """
    Serialize a Result to JSON string.
    
    Args:
        result: The result to serialize
        **kwargs: Additional arguments for json.dumps
    
    Returns:
        JSON string representation
    """
    return json.dumps(result, cls=ResultEncoder, **kwargs)
