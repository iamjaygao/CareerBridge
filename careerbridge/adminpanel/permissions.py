from rest_framework import permissions

class IsAdminOrStaff(permissions.BasePermission):
    """
    自定义权限类：允许管理员角色或员工用户访问
    """
    
    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            return False
        
        # 允许超级用户访问
        if request.user.is_superuser:
            return True
        
        # 允许员工用户访问
        if request.user.is_staff:
            return True
        
        # 允许具有管理员角色的用户访问
        if hasattr(request.user, 'role') and request.user.role in ['admin', 'administrator']:
            return True
        
        return False

class IsAdminUser(permissions.BasePermission):
    """
    自定义权限类：只允许管理员角色用户访问
    """
    
    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            return False
        
        # 允许超级用户访问
        if request.user.is_superuser:
            return True
        
        # 允许具有管理员角色的用户访问
        if hasattr(request.user, 'role') and request.user.role in ['admin', 'administrator']:
            return True
        
        return False 