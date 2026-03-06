"""
Permission and Role-Based Access Control (RBAC) System

Provides:
- Permission enum for fine-grained access control
- Role-Permission mapping
- Permission checking utilities
"""

from enum import Enum
from typing import List, Dict, Set
from dataclasses import dataclass


class Permission(Enum):
    """
    Fine-grained permissions for warehouse operations.
    
    Format: DOMAIN_ACTION
    """
    # Inventory Operations
    INVENTORY_INTAKE = "inventory:intake"
    INVENTORY_DISPATCH = "inventory:dispatch"
    INVENTORY_TRANSFER = "inventory:transfer"
    INVENTORY_SELL = "inventory:sell"
    INVENTORY_ADJUST = "inventory:adjust"
    INVENTORY_VIEW = "inventory:view"
    
    # Stock Management
    STOCK_RESERVE = "stock:reserve"
    STOCK_RELEASE = "stock:release"
    STOCK_VIEW = "stock:view"
    
    # Location Management
    LOCATION_CREATE = "location:create"
    LOCATION_EDIT = "location:edit"
    LOCATION_DELETE = "location:delete"
    LOCATION_VIEW = "location:view"
    
    # Item/Batch Management
    ITEM_CREATE = "item:create"
    ITEM_EDIT = "item:edit"
    ITEM_DELETE = "item:delete"
    ITEM_VIEW = "item:view"
    
    # Batch Operations
    BATCH_CREATE = "batch:create"
    BATCH_EDIT = "batch:edit"
    BATCH_DELETE = "batch:delete"
    BATCH_VIEW = "batch:view"
    
    # Reports
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"
    REPORTS_AUDIT = "reports:audit"
    
    # Manifest Operations
    MANIFEST_CREATE = "manifest:create"
    MANIFEST_VERIFY = "manifest:verify"
    MANIFEST_VIEW = "manifest:view"
    
    # Floor Plan Operations
    FLOORPLAN_CREATE = "floorplan:create"
    FLOORPLAN_EDIT = "floorplan:edit"
    FLOORPLAN_DELETE = "floorplan:delete"
    FLOORPLAN_VIEW = "floorplan:view"
    
    # Zone Operations
    ZONE_CREATE = "zone:create"
    ZONE_EDIT = "zone:edit"
    ZONE_DELETE = "zone:delete"
    ZONE_VIEW = "zone:view"
    
    # User Management (Admin only)
    USERS_CREATE = "users:create"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    USERS_VIEW = "users:view"
    
    # System Operations
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"


class Role(Enum):
    """
    User roles with predefined permission sets.
    """
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    STAFF = "staff"
    VIEWER = "viewer"


# Role-Permission Mapping
# Each role inherits permissions from the role below it
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    
    Role.SUPERVISOR: {
        # All inventory operations
        Permission.INVENTORY_INTAKE,
        Permission.INVENTORY_DISPATCH,
        Permission.INVENTORY_TRANSFER,
        Permission.INVENTORY_SELL,
        Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_VIEW,
        
        # Stock management
        Permission.STOCK_RESERVE,
        Permission.STOCK_RELEASE,
        Permission.STOCK_VIEW,
        
        # Location management
        Permission.LOCATION_CREATE,
        Permission.LOCATION_EDIT,
        Permission.LOCATION_VIEW,
        
        # Item/Batch management
        Permission.ITEM_CREATE,
        Permission.ITEM_EDIT,
        Permission.ITEM_VIEW,
        Permission.BATCH_CREATE,
        Permission.BATCH_EDIT,
        Permission.BATCH_VIEW,
        
        # Reports
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
        
        # Manifest operations
        Permission.MANIFEST_CREATE,
        Permission.MANIFEST_VERIFY,
        Permission.MANIFEST_VIEW,
        
        # Floor plan operations
        Permission.FLOORPLAN_CREATE,
        Permission.FLOORPLAN_EDIT,
        Permission.FLOORPLAN_VIEW,
        
        # Zone operations
        Permission.ZONE_CREATE,
        Permission.ZONE_EDIT,
        Permission.ZONE_VIEW,
        
        # User viewing
        Permission.USERS_VIEW,
    },
    
    Role.STAFF: {
        # Basic inventory operations
        Permission.INVENTORY_INTAKE,
        Permission.INVENTORY_DISPATCH,
        Permission.INVENTORY_TRANSFER,
        Permission.INVENTORY_SELL,
        Permission.INVENTORY_VIEW,
        
        # Stock viewing
        Permission.STOCK_VIEW,
        
        # Location viewing
        Permission.LOCATION_VIEW,
        
        # Item/Batch viewing
        Permission.ITEM_VIEW,
        Permission.BATCH_VIEW,
        
        # Manifest operations
        Permission.MANIFEST_CREATE,
        Permission.MANIFEST_VERIFY,
        Permission.MANIFEST_VIEW,
        
        # Floor plan viewing
        Permission.FLOORPLAN_VIEW,
        
        # Zone viewing
        Permission.ZONE_VIEW,
    },
    
    Role.VIEWER: {
        # Read-only access
        Permission.INVENTORY_VIEW,
        Permission.STOCK_VIEW,
        Permission.LOCATION_VIEW,
        Permission.ITEM_VIEW,
        Permission.BATCH_VIEW,
        Permission.REPORTS_VIEW,
        Permission.MANIFEST_VIEW,
        Permission.FLOORPLAN_VIEW,
        Permission.ZONE_VIEW,
    },
}


@dataclass
class UserRole:
    """User role assignment."""
    user_id: int
    role: Role
    granted_by: int  # User ID who granted this role
    granted_at: str  # ISO timestamp


def get_role_permissions(role: Role) -> Set[Permission]:
    """
    Get all permissions for a role.
    
    Args:
        role: The role to get permissions for
    
    Returns:
        Set of permissions granted to this role
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        role: The role to check
        permission: The permission to check for
    
    Returns:
        True if the role has the permission
    """
    permissions = get_role_permissions(role)
    return permission in permissions


def has_any_permission(role: Role, permissions: List[Permission]) -> bool:
    """
    Check if a role has any of the specified permissions.
    
    Args:
        role: The role to check
        permissions: List of permissions to check
    
    Returns:
        True if the role has at least one permission
    """
    role_permissions = get_role_permissions(role)
    return any(p in role_permissions for p in permissions)


def has_all_permissions(role: Role, permissions: List[Permission]) -> bool:
    """
    Check if a role has all of the specified permissions.
    
    Args:
        role: The role to check
        permissions: List of permissions to check
    
    Returns:
        True if the role has all permissions
    """
    role_permissions = get_role_permissions(role)
    return all(p in role_permissions for p in permissions)


def get_roles_with_permission(permission: Permission) -> List[Role]:
    """
    Get all roles that have a specific permission.
    
    Args:
        permission: The permission to check
    
    Returns:
        List of roles that have this permission
    """
    return [role for role in Role if has_permission(role, permission)]


def get_available_permissions() -> List[Permission]:
    """Get all available permissions."""
    return list(Permission)


def get_available_roles() -> List[Role]:
    """Get all available roles."""
    return list(Role)


# ============================================================================
# Helper Functions for API Use
# ============================================================================

def check_permission(role_name: str, permission_name: str) -> bool:
    """
    Check if a role (by name) has a permission (by name).
    
    Args:
        role_name: Role name string (e.g., 'admin', 'supervisor')
        permission_name: Permission name string (e.g., 'inventory:intake')
    
    Returns:
        True if the role has the permission
    """
    try:
        role = Role(role_name)
        permission = Permission(permission_name)
        return has_permission(role, permission)
    except ValueError:
        return False


def get_role_permissions_dict(role_name: str) -> List[str]:
    """
    Get permissions for a role as a list of strings.
    
    Args:
        role_name: Role name string
    
    Returns:
        List of permission strings
    """
    try:
        role = Role(role_name)
        permissions = get_role_permissions(role)
        return [p.value for p in permissions]
    except ValueError:
        return []


def require_role_for_permission(permission_name: str) -> List[str]:
    """
    Get all roles that have a specific permission.
    
    Args:
        permission_name: Permission name string
    
    Returns:
        List of role names that have this permission
    """
    try:
        permission = Permission(permission_name)
        roles = get_roles_with_permission(permission)
        return [r.value for r in roles]
    except ValueError:
        return []
