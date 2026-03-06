"""
Authorization Decorators for FastAPI Endpoints

Provides:
- Permission-based authorization decorator
- Role-based authorization decorator
- User dependency injection
- Authorization error handling
"""

from functools import wraps
from typing import List, Optional, Union
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from utils.permissions import Permission, Role, has_permission, get_role_permissions
from utils.result import failure, ErrorCode

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"  # TODO: Move to environment variable
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# HTTP Bearer token security
security = HTTPBearer(auto_error=False)


# ============================================================================
# JWT Token Functions
# ============================================================================

def create_jwt_token(user_id: int, username: str, role: str, 
                     expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user_id: User ID
        username: Username
        role: User role
        expires_delta: Optional expiration time delta
    
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    
    to_encode = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================================================
# User Dependency
# ============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from JWT token.
    
    Returns None if no token or invalid token (for optional auth endpoints).
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    if not payload:
        return None
    
    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "role": payload.get("role"),
    }


async def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get current user from JWT token (required).
    
    Raises 401 if no token or invalid token.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail=failure("Authentication required", ErrorCode.UNAUTHORIZED).error
        )
    
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail=failure("Invalid or expired token", ErrorCode.TOKEN_EXPIRED).error
        )
    
    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "role": payload.get("role"),
    }


# ============================================================================
# Authorization Decorators
# ============================================================================

def require_permission(permission: Union[Permission, str]):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        @app.post("/inventory/intake")
        @require_permission(Permission.INVENTORY_INTAKE)
        async def intake(payload: IntakePayload, user: dict = Depends(get_current_user_required)):
            ...
    
    Args:
        permission: Permission enum or string (e.g., 'inventory:intake')
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: dict = Depends(get_current_user_required), **kwargs):
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail=failure("Authentication required", ErrorCode.UNAUTHORIZED).error
                )
            
            # Get permission string
            perm_string = permission.value if isinstance(permission, Permission) else permission
            
            # Check permission
            user_role = user.get("role", "viewer")
            if not has_permission_by_name(user_role, perm_string):
                raise HTTPException(
                    status_code=403,
                    detail=failure(
                        f"Missing permission: {perm_string}",
                        ErrorCode.INSUFFICIENT_ROLE
                    ).error
                )
            
            # Add user info to kwargs
            kwargs["current_user"] = user
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permissions: List[Union[Permission, str]]):
    """
    Decorator to require any one of the specified permissions.
    
    Usage:
        @require_any_permission([Permission.INVENTORY_ADJUST, Permission.INVENTORY_INTAKE])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: dict = Depends(get_current_user_required), **kwargs):
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail=failure("Authentication required", ErrorCode.UNAUTHORIZED).error
                )
            
            user_role = user.get("role", "viewer")
            
            # Check if user has any of the permissions
            has_any = False
            for perm in permissions:
                perm_string = perm.value if isinstance(perm, Permission) else perm
                if has_permission_by_name(user_role, perm_string):
                    has_any = True
                    break
            
            if not has_any:
                perm_strings = [
                    p.value if isinstance(p, Permission) else p 
                    for p in permissions
                ]
                raise HTTPException(
                    status_code=403,
                    detail=failure(
                        f"Requires one of: {', '.join(perm_strings)}",
                        ErrorCode.INSUFFICIENT_ROLE
                    ).error
                )
            
            kwargs["current_user"] = user
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: Union[Role, str]):
    """
    Decorator to require a specific role.
    
    Usage:
        @require_role(Role.ADMIN)
        # or
        @require_role('admin')
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: dict = Depends(get_current_user_required), **kwargs):
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail=failure("Authentication required", ErrorCode.UNAUTHORIZED).error
                )
            
            user_role = user.get("role", "")
            required_role = role.value if isinstance(role, Role) else role
            
            if user_role.lower() != required_role.lower():
                raise HTTPException(
                    status_code=403,
                    detail=failure(
                        f"Requires role: {required_role}",
                        ErrorCode.INSUFFICIENT_ROLE
                    ).error
                )
            
            kwargs["current_user"] = user
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_role(roles: List[Union[Role, str]]):
    """
    Decorator to require any one of the specified roles.
    
    Usage:
        @require_any_role([Role.ADMIN, Role.SUPERVISOR])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: dict = Depends(get_current_user_required), **kwargs):
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail=failure("Authentication required", ErrorCode.UNAUTHORIZED).error
                )
            
            user_role = user.get("role", "")
            required_roles = [r.value if isinstance(r, Role) else r for r in roles]
            
            if user_role.lower() not in [r.lower() for r in required_roles]:
                raise HTTPException(
                    status_code=403,
                    detail=failure(
                        f"Requires one of roles: {', '.join(required_roles)}",
                        ErrorCode.INSUFFICIENT_ROLE
                    ).error
                )
            
            kwargs["current_user"] = user
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# Helper Functions
# ============================================================================

def has_permission_by_name(role_name: str, permission_name: str) -> bool:
    """
    Check if a role (by name string) has a permission (by name string).
    
    Args:
        role_name: Role name (e.g., 'admin', 'supervisor')
        permission_name: Permission name (e.g., 'inventory:intake')
    
    Returns:
        True if role has permission
    """
    try:
        role = Role(role_name.lower())
        permission = Permission(permission_name.lower())
        return has_permission(role, permission)
    except ValueError:
        return False


def get_user_permissions_list(role_name: str) -> List[str]:
    """
    Get all permissions for a role as a list of strings.
    
    Args:
        role_name: Role name
    
    Returns:
        List of permission strings
    """
    try:
        role = Role(role_name.lower())
        perms = get_role_permissions(role)
        return [p.value for p in perms]
    except ValueError:
        return []


# ============================================================================
# Optional Auth Decorator (for endpoints that work with or without auth)
# ============================================================================

def optional_auth(func):
    """
    Decorator for endpoints that work with or without authentication.
    
    User info will be passed if available, None otherwise.
    """
    @wraps(func)
    async def wrapper(*args, user: Optional[dict] = Depends(get_current_user), **kwargs):
        kwargs["current_user"] = user
        return await func(*args, **kwargs)
    
    return wrapper
