"""
Unit tests for Authorization and JWT Authentication.

Tests cover:
- JWT token creation and validation
- Authorization decorators
- Permission checking in endpoints
- Role-based access control
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth import (
    create_jwt_token,
    decode_jwt_token,
    require_permission,
    require_role,
    require_any_permission,
    require_any_role,
    get_current_user,
    get_current_user_required,
    has_permission_by_name,
    get_user_permissions_list,
    JWT_SECRET,
)
from utils.permissions import Permission, Role


class TestJWTToken:
    """Tests for JWT token functions."""
    
    def test_create_token(self):
        """Test creating a JWT token."""
        token = create_jwt_token(
            user_id=1,
            username="testuser",
            role="staff"
        )
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
    
    def test_decode_token(self):
        """Test decoding a valid JWT token."""
        token = create_jwt_token(
            user_id=123,
            username="adminuser",
            role="admin"
        )
        
        payload = decode_jwt_token(token)
        
        assert payload is not None
        assert payload["user_id"] == 123
        assert payload["username"] == "adminuser"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        token = create_jwt_token(
            user_id=1,
            username="testuser",
            role="staff",
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        payload = decode_jwt_token(token)
        
        assert payload is None
    
    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = decode_jwt_token("invalid.token.here")
        assert payload is None
    
    def test_token_expiry(self):
        """Test token expiry with custom delta."""
        token = create_jwt_token(
            user_id=1,
            username="testuser",
            role="staff",
            expires_delta=timedelta(hours=1)
        )
        
        payload = decode_jwt_token(token)
        assert payload is not None
        
        # Check expiry is approximately 1 hour from now
        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])
        delta = exp - iat
        assert delta.total_seconds() >= 3600


class TestHasPermissionByName:
    """Tests for has_permission_by_name helper."""
    
    def test_admin_permissions(self):
        """Test admin has all permissions."""
        assert has_permission_by_name("admin", "inventory:intake") is True
        assert has_permission_by_name("admin", "users:create") is True
        assert has_permission_by_name("admin", "system:config") is True
    
    def test_staff_permissions(self):
        """Test staff permissions."""
        assert has_permission_by_name("staff", "inventory:intake") is True
        assert has_permission_by_name("staff", "inventory:view") is True
        assert has_permission_by_name("staff", "inventory:adjust") is False
    
    def test_viewer_permissions(self):
        """Test viewer read-only permissions."""
        assert has_permission_by_name("viewer", "inventory:view") is True
        assert has_permission_by_name("viewer", "reports:view") is True
        assert has_permission_by_name("viewer", "inventory:adjust") is False
    
    def test_invalid_role(self):
        """Test invalid role returns False."""
        assert has_permission_by_name("invalid_role", "inventory:intake") is False
    
    def test_invalid_permission(self):
        """Test invalid permission returns False."""
        assert has_permission_by_name("admin", "invalid:permission") is False


class TestGetUserPermissionsList:
    """Tests for get_user_permissions_list helper."""
    
    def test_get_admin_permissions(self):
        """Test getting admin permissions."""
        perms = get_user_permissions_list("admin")
        
        assert isinstance(perms, list)
        assert len(perms) > 40  # Admin has all permissions
        assert "inventory:intake" in perms
        assert "users:create" in perms
    
    def test_get_viewer_permissions(self):
        """Test getting viewer permissions."""
        perms = get_user_permissions_list("viewer")
        
        assert isinstance(perms, list)
        assert len(perms) < 15  # Viewer has limited permissions
        assert "inventory:view" in perms
        assert "inventory:adjust" not in perms
    
    def test_get_invalid_role_permissions(self):
        """Test getting permissions for invalid role."""
        perms = get_user_permissions_list("invalid_role")
        assert perms == []


class TestAuthDecorators:
    """Tests for authorization decorators."""
    
    @pytest.mark.asyncio
    @patch('utils.auth.get_current_user_required')
    async def test_require_permission_success(self, mock_get_user):
        """Test require_permission with valid user."""
        from utils.auth import require_permission
        
        mock_get_user.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "staff"
        }
        
        @require_permission(Permission.INVENTORY_INTAKE)
        async def test_endpoint(current_user):
            return {"success": True}
        
        result = await test_endpoint()
        assert result["success"] is True
        assert result.get("current_user") is not None
    
    @pytest.mark.asyncio
    @patch('utils.auth.get_current_user_required')
    async def test_require_permission_denied(self, mock_get_user):
        """Test require_permission with insufficient permissions."""
        from utils.auth import require_permission
        
        mock_get_user.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "viewer"
        }
        
        @require_permission(Permission.INVENTORY_ADJUST)
        async def test_endpoint(current_user):
            return {"success": True}
        
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint()
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    @patch('utils.auth.get_current_user_required')
    async def test_require_role_success(self, mock_get_user):
        """Test require_role with matching role."""
        from utils.auth import require_role
        
        mock_get_user.return_value = {
            "user_id": 1,
            "username": "adminuser",
            "role": "admin"
        }
        
        @require_role(Role.ADMIN)
        async def test_endpoint(current_user):
            return {"success": True}
        
        result = await test_endpoint()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('utils.auth.get_current_user_required')
    async def test_require_role_denied(self, mock_get_user):
        """Test require_role with non-matching role."""
        from utils.auth import require_role
        
        mock_get_user.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "staff"
        }
        
        @require_role(Role.ADMIN)
        async def test_endpoint(current_user):
            return {"success": True}
        
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint()
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    @patch('utils.auth.get_current_user_required')
    async def test_require_any_permission_success(self, mock_get_user):
        """Test require_any_permission with one matching permission."""
        from utils.auth import require_any_permission
        
        mock_get_user.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "staff"
        }
        
        @require_any_permission([
            Permission.INVENTORY_ADJUST,  # Staff doesn't have
            Permission.INVENTORY_INTAKE   # Staff has this
        ])
        async def test_endpoint(current_user):
            return {"success": True}
        
        result = await test_endpoint()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('utils.auth.get_current_user_required')
    async def test_require_any_role_success(self, mock_get_user):
        """Test require_any_role with one matching role."""
        from utils.auth import require_any_role
        
        mock_get_user.return_value = {
            "user_id": 1,
            "username": "supervisoruser",
            "role": "supervisor"
        }
        
        @require_any_role([Role.ADMIN, Role.SUPERVISOR])
        async def test_endpoint(current_user):
            return {"success": True}
        
        result = await test_endpoint()
        assert result["success"] is True


class TestCurrentUserDependency:
    """Tests for current user dependency."""
    
    @pytest.mark.asyncio
    @patch('utils.auth.decode_jwt_token')
    @patch('utils.auth.security')
    async def test_get_current_user_with_token(self, mock_security, mock_decode):
        """Test getting current user with valid token."""
        from utils.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="fake_token"
        )
        mock_decode.return_value = {
            "user_id": 123,
            "username": "testuser",
            "role": "staff"
        }
        
        # Note: This is a simplified test - actual usage involves FastAPI DI
        user = await get_current_user(credentials=mock_credentials)
        
        assert user is not None
        assert user["user_id"] == 123
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        """Test getting current user without token."""
        from utils.auth import get_current_user
        
        user = await get_current_user(credentials=None)
        assert user is None
    
    @pytest.mark.asyncio
    @patch('utils.auth.decode_jwt_token')
    async def test_get_current_user_required_with_token(self, mock_decode):
        """Test getting required current user with valid token."""
        from utils.auth import get_current_user_required
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="fake_token"
        )
        mock_decode.return_value = {
            "user_id": 123,
            "username": "testuser",
            "role": "staff"
        }
        
        user = await get_current_user_required(credentials=mock_credentials)
        
        assert user is not None
        assert user["user_id"] == 123
    
    @pytest.mark.asyncio
    async def test_get_current_user_required_no_token(self):
        """Test getting required current user without token."""
        from utils.auth import get_current_user_required
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_required(credentials=None)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    @patch('utils.auth.decode_jwt_token')
    async def test_get_current_user_required_invalid_token(self, mock_decode):
        """Test getting required current user with invalid token."""
        from utils.auth import get_current_user_required
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="fake_token"
        )
        mock_decode.return_value = None  # Invalid token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_required(credentials=mock_credentials)
        
        assert exc_info.value.status_code == 401


class TestAuthIntegration:
    """Integration tests for auth system."""
    
    def test_token_contains_all_claims(self):
        """Test JWT token contains all required claims."""
        token = create_jwt_token(
            user_id=42,
            username="integration_test",
            role="supervisor"
        )
        
        payload = decode_jwt_token(token)
        
        assert payload["user_id"] == 42
        assert payload["username"] == "integration_test"
        assert payload["role"] == "supervisor"
        assert payload["exp"] > payload["iat"]
        assert payload["type"] == "access"
    
    def test_role_hierarchy_enforcement(self):
        """Test role hierarchy is enforced in permissions."""
        # Admin should have access to everything
        assert has_permission_by_name("admin", "users:create")
        assert has_permission_by_name("admin", "inventory:adjust")
        
        # Supervisor should not have user creation
        assert not has_permission_by_name("supervisor", "users:create")
        assert has_permission_by_name("supervisor", "inventory:adjust")
        
        # Staff should not have adjustments
        assert not has_permission_by_name("staff", "inventory:adjust")
        assert has_permission_by_name("staff", "inventory:intake")
        
        # Viewer should only have view permissions
        assert has_permission_by_name("viewer", "inventory:view")
        assert not has_permission_by_name("viewer", "inventory:intake")
