from rest_framework import permissions


def is_superadmin(user):
    """
    Check if user is a superadmin (root platform control).
    """
    if not user or not user.is_authenticated:
        return False
    return hasattr(user, 'role') and user.role == 'superadmin'


def is_admin_level(user):
    """
    Check if user is admin or superadmin (operational management level).
    """
    if not user or not user.is_authenticated:
        return False
    if hasattr(user, 'role'):
        return user.role in ('admin', 'superadmin')
    return False


def user_has_role(user, *roles):
    """
    Helper function to check if user has any of the specified roles.
    Superadmin is treated as a global wildcard and can access any role.
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superadmin can access everything
    if is_superadmin(user):
        return True
    
    # Check if user has one of the specified roles
    if hasattr(user, 'role') and user.role in roles:
        return True
    
    return False


class IsAdminOrStaff(permissions.BasePermission):
    """
    自定义权限类：允许管理员角色或员工用户访问
    Superadmin 可以访问所有内容
    """
    
    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            return False
        
        # 允许超级用户访问
        if request.user.is_superuser:
            return True
        
        # 允许 superadmin 角色访问
        if user_has_role(request.user, 'superadmin'):
            return True
        
        # 允许员工用户访问
        if request.user.is_staff:
            return True
        
        # 允许具有管理员或员工角色的用户访问
        if user_has_role(request.user, 'admin', 'staff'):
            return True
        
        return False


class IsAdminUser(permissions.BasePermission):
    """
    自定义权限类：只允许管理员角色用户访问
    Superadmin 可以访问所有内容
    """
    
    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            return False
        
        # 允许超级用户访问
        if request.user.is_superuser:
            return True
        
        # 允许 superadmin 角色访问
        if user_has_role(request.user, 'superadmin'):
            return True
        
        # 允许具有管理员角色的用户访问
        if user_has_role(request.user, 'admin'):
            return True
        
        return False


class IsMentor(permissions.BasePermission):
    """
    自定义权限类：只允许导师角色用户访问
    Superadmin 可以访问所有内容
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superadmin can access everything
        if user_has_role(request.user, 'superadmin'):
            return True
        
        # Check if user is a mentor
        if user_has_role(request.user, 'mentor'):
            return True
        
        return False


class IsStaff(permissions.BasePermission):
    """
    自定义权限类：只允许员工角色用户访问
    Superadmin 可以访问所有内容
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superadmin can access everything
        if user_has_role(request.user, 'superadmin'):
            return True
        
        # Check if user is staff or admin
        if user_has_role(request.user, 'staff', 'admin'):
            return True
        
        return False


class IsStudent(permissions.BasePermission):
    """
    自定义权限类：只允许学生角色用户访问
    Superadmin 可以访问所有内容
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superadmin can access everything
        if user_has_role(request.user, 'superadmin'):
            return True
        
        # Check if user is a student
        if user_has_role(request.user, 'student'):
            return True
        
        return False


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Permission class: Only admin or superadmin can access
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if user_has_role(request.user, 'admin', 'superadmin'):
            return True
        
        return False 