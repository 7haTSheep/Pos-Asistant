"""
Utility modules for POS-Assistant server.

Provides common functionality used across the application:
- Result pattern for error handling
- Error codes enumeration
- Permission and role-based access control
- Authentication helpers
- Logging configuration
"""

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
    ResultEncoder,
)

from utils.permissions import (
    Permission,
    Role,
    has_permission,
    has_any_permission,
    has_all_permissions,
    get_role_permissions,
    check_permission,
    get_role_permissions_dict,
    require_role_for_permission,
)

__all__ = [
    # Result pattern
    'Result',
    'Success',
    'Failure',
    'ErrorCode',
    'success',
    'failure',
    'ResultExtensions',
    'result_to_http_response',
    'result_to_json',
    'ResultEncoder',
    
    # Permissions
    'Permission',
    'Role',
    'has_permission',
    'has_any_permission',
    'has_all_permissions',
    'get_role_permissions',
    'check_permission',
    'get_role_permissions_dict',
    'require_role_for_permission',
]
