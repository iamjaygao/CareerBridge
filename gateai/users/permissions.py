from rest_framework import permissions

def user_has_capability(user, cap_code):
    """
    Standalone helper to check if a user has a specific admin capability.
    Superusers automatically have all capabilities.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
        
    # Check if the user has the capability
    # Using the has_capability method defined on the User model
    return user.has_capability(cap_code)


class HasAdminCapability(permissions.BasePermission):
    """
    DRF permission class to check for a specific AdminCapability.
    Usage:
        permission_classes = [HasAdminCapability]
        required_capability = 'mock.manage'
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Get the required capability from the view
        required_capability = getattr(view, 'required_capability', None)
        if not required_capability:
            return True  # If no capability is required, allow access
            
        return user_has_capability(request.user, required_capability)
