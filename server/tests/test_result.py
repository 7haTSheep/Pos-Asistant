"""
Unit tests for Result pattern implementation.

Run with: pytest tests/test_result.py -v
"""

import pytest
from utils.result import (
    Result,
    Success,
    Failure,
    ErrorCode,
    success,
    failure,
    ResultExtensions,
    result_to_http_response,
    result_to_json,
)


class TestSuccess:
    """Tests for Success type."""
    
    def test_success_creation(self):
        """Test creating a successful result."""
        result = Success(value=42)
        assert result.is_success is True
        assert result.is_failure is False
        assert result.value == 42
        assert result.error is None
    
    def test_success_with_message(self):
        """Test success with custom message."""
        result = Success(value="data", message="Operation completed")
        assert result.message == "Operation completed"
    
    def test_success_with_metadata(self):
        """Test success with metadata."""
        result = Success(
            value={"id": 1},
            metadata={"created": True, "user_id": 123}
        )
        assert result.metadata["created"] is True
        assert result.metadata["user_id"] == 123
    
    def test_success_bool(self):
        """Test boolean conversion."""
        result = Success(value=1)
        assert bool(result) is True
    
    def test_success_to_dict(self):
        """Test dictionary conversion."""
        result = Success(value=100, message="Test")
        data = result.to_dict()
        assert data["is_success"] is True
        assert data["value"] == 100
        assert data["message"] == "Test"


class TestFailure:
    """Tests for Failure type."""
    
    def test_failure_creation(self):
        """Test creating a failure result."""
        result = Failure(error="Something went wrong")
        assert result.is_success is False
        assert result.is_failure is True
        assert result.error == "Something went wrong"
        assert result.value is None
    
    def test_failure_with_error_code(self):
        """Test failure with error code."""
        result = Failure(
            error="Item not found",
            error_code=ErrorCode.ITEM_NOT_FOUND
        )
        assert result.error_code == ErrorCode.ITEM_NOT_FOUND
        assert result.error_code.code == "INV-008"
        assert result.error_code.http_status == 404
    
    def test_failure_with_details(self):
        """Test failure with additional details."""
        result = Failure(
            error="Validation failed",
            details={"field": "quantity", "reason": "must be positive"}
        )
        assert result.details["field"] == "quantity"
    
    def test_failure_bool(self):
        """Test boolean conversion."""
        result = Failure(error="error")
        assert bool(result) is False
    
    def test_failure_to_dict(self):
        """Test dictionary conversion."""
        result = Failure(
            error="Test error",
            error_code=ErrorCode.INVALID_BATCH
        )
        data = result.to_dict()
        assert data["is_success"] is False
        assert data["error"] == "Test error"
        assert data["error_code"] == "INV-003"
        assert data["http_status"] == 400


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_success_helper(self):
        """Test success() helper function."""
        result = success(42, message="Done")
        assert isinstance(result, Success)
        assert result.value == 42
        assert result.message == "Done"
    
    def test_failure_helper(self):
        """Test failure() helper function."""
        result = failure("Error", ErrorCode.DATABASE_ERROR)
        assert isinstance(result, Failure)
        assert result.error == "Error"
        assert result.error_code == ErrorCode.DATABASE_ERROR


class TestErrorCode:
    """Tests for ErrorCode enum."""
    
    def test_error_code_values(self):
        """Test error code properties."""
        assert ErrorCode.SUCCESS.code == "OK"
        assert ErrorCode.SUCCESS.http_status == 200
        
        assert ErrorCode.ITEM_NOT_FOUND.code == "INV-008"
        assert ErrorCode.ITEM_NOT_FOUND.http_status == 404
        
        assert ErrorCode.DATABASE_ERROR.http_status == 500
    
    def test_error_code_from_string(self):
        """Test parsing error code from string."""
        code = ErrorCode.from_string("INV-001")
        assert code == ErrorCode.INSUFFICIENT_STOCK
    
    def test_error_code_from_string_unknown(self):
        """Test parsing unknown error code."""
        code = ErrorCode.from_string("UNKNOWN")
        assert code == ErrorCode.INTERNAL_ERROR
    
    def test_error_code_str(self):
        """Test string conversion."""
        assert str(ErrorCode.SUCCESS) == "OK"
        assert str(ErrorCode.ITEM_NOT_FOUND) == "INV-008"


class TestResultExtensions:
    """Tests for ResultExtensions."""
    
    def test_map_success(self):
        """Test mapping over success."""
        result = Success(value=5)
        mapped = ResultExtensions.map(result, lambda x: x * 2)
        assert mapped.value == 10
        assert mapped.is_success is True
    
    def test_map_failure(self):
        """Test mapping over failure (no-op)."""
        result = Failure(error="error")
        mapped = ResultExtensions.map(result, lambda x: x * 2)
        assert mapped.is_failure is True
        assert mapped.error == "error"
    
    def test_bind_success(self):
        """Test binding over success."""
        def divide_by_two(x):
            return Success(value=x / 2)
        
        result = Success(value=10)
        bound = ResultExtensions.bind(result, divide_by_two)
        assert bound.value == 5.0
    
    def test_bind_failure(self):
        """Test binding over failure (short-circuit)."""
        def should_not_be_called(x):
            return Success(value=x * 2)
        
        result = Failure(error="error")
        bound = ResultExtensions.bind(result, should_not_be_called)
        assert bound.is_failure is True
    
    def test_unwrap_success(self):
        """Test unwrapping success."""
        result = Success(value=42)
        value = ResultExtensions.unwrap(result, default=0)
        assert value == 42
    
    def test_unwrap_failure(self):
        """Test unwrapping failure."""
        result = Failure(error="error")
        value = ResultExtensions.unwrap(result, default=999)
        assert value == 999
    
    def test_unwrap_or_raise_success(self):
        """Test unwrap or raise with success."""
        result = Success(value=100)
        value = ResultExtensions.unwrap_or_raise(result)
        assert value == 100
    
    def test_unwrap_or_raise_failure(self):
        """Test unwrap or raise with failure."""
        result = Failure(error="test error")
        with pytest.raises(ValueError, match="test error"):
            ResultExtensions.unwrap_or_raise(result)
    
    def test_combine_success(self):
        """Test combining multiple success results."""
        results = [
            Success(value=1),
            Success(value=2),
            Success(value=3),
        ]
        combined = ResultExtensions.combine(results)
        assert combined.is_success is True
        assert combined.value == [1, 2, 3]
    
    def test_combine_failure(self):
        """Test combining with one failure."""
        results = [
            Success(value=1),
            Failure(error="middle error"),
            Success(value=3),
        ]
        combined = ResultExtensions.combine(results)
        assert combined.is_failure is True
        assert combined.error == "middle error"


class TestHTTPResponseHelpers:
    """Tests for HTTP response helpers."""
    
    def test_result_to_http_response_success(self):
        """Test converting success to HTTP response."""
        result = Success(value={"id": 1})
        body, status = result_to_http_response(result)
        assert body["is_success"] is True
        assert status == 200
    
    def test_result_to_http_response_failure(self):
        """Test converting failure to HTTP response."""
        result = Failure(
            error="Not found",
            error_code=ErrorCode.ITEM_NOT_FOUND
        )
        body, status = result_to_http_response(result)
        assert body["is_success"] is False
        assert body["error"] == "Not found"
        assert status == 404


class TestJSONSerialization:
    """Tests for JSON serialization."""
    
    def test_result_to_json_success(self):
        """Test JSON serialization of success."""
        result = Success(value=42, message="Test")
        json_str = result_to_json(result)
        assert "is_success" in json_str
        assert "42" in json_str
    
    def test_result_to_json_failure(self):
        """Test JSON serialization of failure."""
        result = Failure(error="Error", error_code=ErrorCode.DATABASE_ERROR)
        json_str = result_to_json(result)
        assert "is_success" in json_str
        assert "Error" in json_str
        assert "SRV-001" in json_str


class TestUsageExamples:
    """Integration tests showing common usage patterns."""
    
    def test_database_operation_pattern(self):
        """Test pattern for database operations."""
        def get_item_from_db(sku: str) -> Result[dict, str]:
            # Simulated database lookup
            if sku == "VALID-001":
                return success({"sku": sku, "name": "Test Item"})
            return failure(f"Item '{sku}' not found", ErrorCode.ITEM_NOT_FOUND)
        
        # Test valid SKU
        result = get_item_from_db("VALID-001")
        assert result.is_success is True
        assert result.value["sku"] == "VALID-001"
        
        # Test invalid SKU
        result = get_item_from_db("INVALID-001")
        assert result.is_failure is True
        assert result.error_code == ErrorCode.ITEM_NOT_FOUND
    
    def test_validation_pattern(self):
        """Test pattern for validation."""
        def validate_quantity(qty: int) -> Result[int, str]:
            if qty <= 0:
                return failure("Quantity must be positive", ErrorCode.INVALID_QUANTITY)
            if qty > 10000:
                return failure("Quantity exceeds maximum", ErrorCode.CAPACITY_EXCEEDED)
            return success(qty)
        
        # Test valid quantity
        result = validate_quantity(100)
        assert result.is_success is True
        
        # Test invalid quantities
        result = validate_quantity(0)
        assert result.is_failure is True
        assert result.error_code == ErrorCode.INVALID_QUANTITY
        
        result = validate_quantity(99999)
        assert result.is_failure is True
        assert result.error_code == ErrorCode.CAPACITY_EXCEEDED
    
    def test_chained_operations_pattern(self):
        """Test pattern for chained operations."""
        def step1() -> Result[int, str]:
            return success(10)
        
        def step2(value: int) -> Result[int, str]:
            if value > 5:
                return success(value * 2)
            return failure("Value too small")
        
        def step3(value: int) -> Result[int, str]:
            return success(value + 100)
        
        # Chain operations
        result = step1()
        if result.is_success:
            result = step2(result.value)
        if result.is_success:
            result = step3(result.value)
        
        assert result.is_success is True
        assert result.value == 120  # (10 * 2) + 100
