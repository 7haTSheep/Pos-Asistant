"""
Unit tests for Permission and RBAC system.

Tests cover:
- Permission enum
- Role-Permission mapping
- Permission checking functions
- Database role methods
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    get_available_permissions,
    get_available_roles,
)


class TestPermissionEnum:
    """Tests for Permission enum."""
    
    def test_permission_values(self):
        """Test permission string values."""
        assert Permission.INVENTORY_INTAKE.value == "inventory:intake"
        assert Permission.INVENTORY_ADJUST.value == "inventory:adjust"
        assert Permission.USERS_CREATE.value == "users:create"
    
    def test_permission_categories(self):
        """Test permission categories exist."""
        # Inventory
        assert Permission.INVENTORY_VIEW in Permission
        assert Permission.INVENTORY_INTAKE in Permission
        
        # Stock
        assert Permission.STOCK_VIEW in Permission
        assert Permission.STOCK_RESERVE in Permission
        
        # Users
        assert Permission.USERS_VIEW in Permission
        assert Permission.USERS_CREATE in Permission
        
        # Reports
        assert Permission.REPORTS_VIEW in Permission
        assert Permission.REPORTS_EXPORT in Permission


class TestRoleEnum:
    """Tests for Role enum."""
    
    def test_role_values(self):
        """Test role string values."""
        assert Role.ADMIN.value == "admin"
        assert Role.SUPERVISOR.value == "supervisor"
        assert Role.STAFF.value == "staff"
        assert Role.VIEWER.value == "viewer"
    
    def test_all_roles_available(self):
        """Test all roles are available."""
        roles = get_available_roles()
        assert len(roles) == 4
        assert Role.ADMIN in roles
        assert Role.VIEWER in roles


class TestRolePermissions:
    """Tests for role-permission mapping."""
    
    def test_admin_has_all_permissions(self):
        """Test admin role has all permissions."""
        admin_perms = get_role_permissions(Role.ADMIN)
        all_perms = set(Permission)
        assert admin_perms == all_perms
        assert len(admin_perms) >= 40  # Should have many permissions
    
    def test_viewer_has_limited_permissions(self):
        """Test viewer role has limited (read-only) permissions."""
        viewer_perms = get_role_permissions(Role.VIEWER)
        
        # Should have view permissions
        assert Permission.INVENTORY_VIEW in viewer_perms
        assert Permission.STOCK_VIEW in viewer_perms
        assert Permission.REPORTS_VIEW in viewer_perms
        
        # Should NOT have write permissions
        assert Permission.INVENTORY_ADJUST not in viewer_perms
        assert Permission.USERS_CREATE not in viewer_perms
        assert Permission.ITEM_DELETE not in viewer_perms
    
    def test_staff_has_operational_permissions(self):
        """Test staff role has operational permissions."""
        staff_perms = get_role_permissions(Role.STAFF)
        
        # Should have basic operations
        assert Permission.INVENTORY_INTAKE in staff_perms
        assert Permission.INVENTORY_DISPATCH in staff_perms
        assert Permission.MANIFEST_CREATE in staff_perms
        
        # Should NOT have admin operations
        assert Permission.USERS_CREATE not in staff_perms
        assert Permission.SYSTEM_CONFIG not in staff_perms
    
    def test_supervisor_has_extended_permissions(self):
        """Test supervisor role has extended permissions."""
        supervisor_perms = get_role_permissions(Role.SUPERVISOR)
        
        # Should have staff permissions plus more
        assert Permission.INVENTORY_ADJUST in supervisor_perms
        assert Permission.ITEM_CREATE in supervisor_perms
        assert Permission.REPORTS_EXPORT in supervisor_perms
        
        # Should NOT have admin-only
        assert Permission.USERS_CREATE not in supervisor_perms
        assert Permission.SYSTEM_CONFIG not in supervisor_perms


class TestPermissionChecking:
    """Tests for permission checking functions."""
    
    def test_has_permission_admin(self):
        """Test has_permission for admin."""
        assert has_permission(Role.ADMIN, Permission.INVENTORY_INTAKE) is True
        assert has_permission(Role.ADMIN, Permission.USERS_CREATE) is True
    
    def test_has_permission_viewer(self):
        """Test has_permission for viewer."""
        assert has_permission(Role.VIEWER, Permission.INVENTORY_VIEW) is True
        assert has_permission(Role.VIEWER, Permission.INVENTORY_ADJUST) is False
    
    def test_has_any_permission(self):
        """Test has_any_permission function."""
        permissions = [Permission.USERS_CREATE, Permission.SYSTEM_CONFIG]
        
        # Admin should have at least one
        assert has_any_permission(Role.ADMIN, permissions) is True
        
        # Staff should have neither
        assert has_any_permission(Role.STAFF, permissions) is False
    
    def test_has_all_permissions(self):
        """Test has_all_permissions function."""
        permissions = [
            Permission.INVENTORY_VIEW,
            Permission.STOCK_VIEW,
            Permission.REPORTS_VIEW
        ]
        
        # Admin should have all
        assert has_all_permissions(Role.ADMIN, permissions) is True
        
        # Viewer should have all (all are view permissions)
        assert has_all_permissions(Role.VIEWER, permissions) is True
        
        # Add a non-view permission
        permissions.append(Permission.INVENTORY_ADJUST)
        
        # Viewer should not have all now
        assert has_all_permissions(Role.VIEWER, permissions) is False


class TestCheckPermissionFunction:
    """Tests for check_permission helper function."""
    
    def test_check_permission_by_string(self):
        """Test checking permission with string names."""
        assert check_permission('admin', 'inventory:intake') is True
        assert check_permission('supervisor', 'inventory:adjust') is True
        assert check_permission('staff', 'inventory:intake') is True
        assert check_permission('viewer', 'inventory:view') is True
        assert check_permission('viewer', 'inventory:adjust') is False
    
    def test_check_permission_invalid_role(self):
        """Test checking permission with invalid role."""
        assert check_permission('invalid_role', 'inventory:intake') is False
    
    def test_check_permission_invalid_permission(self):
        """Test checking permission with invalid permission."""
        assert check_permission('admin', 'invalid:permission') is False


class TestGetRolePermissionsDict:
    """Tests for get_role_permissions_dict function."""
    
    def test_get_permissions_as_strings(self):
        """Test getting permissions as string list."""
        perms = get_role_permissions_dict('viewer')
        
        assert isinstance(perms, list)
        assert all(isinstance(p, str) for p in perms)
        assert 'inventory:view' in perms
        assert 'inventory:adjust' not in perms
    
    def test_get_permissions_invalid_role(self):
        """Test getting permissions for invalid role."""
        perms = get_role_permissions_dict('invalid_role')
        assert perms == []


class TestRequireRoleForPermission:
    """Tests for require_role_for_permission function."""
    
    def test_get_roles_with_permission(self):
        """Test getting all roles that have a permission."""
        roles = require_role_for_permission('inventory:intake')
        
        assert isinstance(roles, list)
        assert 'admin' in roles
        assert 'supervisor' in roles
        assert 'staff' in roles
        assert 'viewer' not in roles  # Viewer doesn't have intake
    
    def test_get_roles_for_admin_only_permission(self):
        """Test getting roles for admin-only permission."""
        roles = require_role_for_permission('users:create')
        
        assert 'admin' in roles
        assert 'supervisor' not in roles
        assert 'staff' not in roles


class TestDatabaseRoleMethods:
    """Tests for database role methods."""
    
    @patch('database.mysql.connector')
    def test_get_user_role(self, mock_connector):
        """Test getting user role from database."""
        from database import Database
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('supervisor',)
        
        db = Database()
        role = db.get_user_role(1)
        
        assert role == 'supervisor'
    
    @patch('database.mysql.connector')
    def test_update_user_role(self, mock_connector):
        """Test updating user role."""
        from database import Database
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        
        db = Database()
        result = db.update_user_role(1, 'admin')
        
        assert result is True
        mock_cursor.execute.assert_called_once()
    
    @patch('database.mysql.connector')
    @patch('utils.permissions.check_permission')
    def test_user_has_permission(self, mock_check, mock_connector):
        """Test checking user permission."""
        from database import Database
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('staff',)
        mock_check.return_value = True
        
        db = Database()
        result = db.user_has_permission(1, 'inventory:intake')
        
        assert result is True
        mock_check.assert_called_once_with('staff', 'inventory:intake')
    
    @patch('database.mysql.connector')
    @patch('utils.permissions.get_role_permissions_dict')
    def test_get_user_permissions(self, mock_get_perms, mock_connector):
        """Test getting user permissions."""
        from database import Database
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('supervisor',)
        mock_get_perms.return_value = ['inventory:intake', 'inventory:view']
        
        db = Database()
        perms = db.get_user_permissions(1)
        
        assert isinstance(perms, list)
        assert len(perms) == 2
    
    @patch('database.mysql.connector')
    def test_create_user_with_role(self, mock_connector):
        """Test creating user with specific role."""
        from database import Database
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 123
        
        db = Database()
        user_id = db.create_user_with_role('testuser', 'hashedpw', 'staff')
        
        assert user_id == 123
        mock_cursor.execute.assert_called_once()


class TestPermissionIntegration:
    """Integration tests for permission system."""
    
    def test_role_hierarchy(self):
        """Test role permission hierarchy."""
        # Admin should have more permissions than supervisor
        admin_perms = get_role_permissions(Role.ADMIN)
        supervisor_perms = get_role_permissions(Role.SUPERVISOR)
        staff_perms = get_role_permissions(Role.STAFF)
        viewer_perms = get_role_permissions(Role.VIEWER)
        
        assert len(admin_perms) > len(supervisor_perms)
        assert len(supervisor_perms) > len(staff_perms)
        assert len(staff_perms) > len(viewer_perms)
    
    def test_permission_format(self):
        """Test all permissions follow format."""
        for permission in Permission:
            assert ':' in permission.value
            parts = permission.value.split(':')
            assert len(parts) == 2
            assert len(parts[0]) > 0  # Domain
            assert len(parts[1]) > 0  # Action
    
    def test_all_permissions_covered(self):
        """Test all permissions are assigned to at least one role."""
        all_perms = set(Permission)
        assigned_perms = set()
        
        for role in Role:
            assigned_perms.update(get_role_permissions(role))
        
        # All permissions should be assigned to at least admin
        assert all_perms == assigned_perms
