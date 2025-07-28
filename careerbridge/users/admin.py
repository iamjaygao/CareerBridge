from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register the costom User model with the Django admin site
# We import "admin" for registration, "UserAdmin" as base admin class
# and our own custom 'User' model, By using @admin.register(User)
# We bind the User model to the CustomUserAdmin class, which inherits from UserAdmin
# and overrides default admin behavior to custmoize how user data
# is displayed and managed in the admin interface.

# register the User model with the admin site
@admin.register(User)

class CustomUserAdmin(UserAdmin): # inherit from the built-in UserAdmin

    # explicitly specify that this admin interface is for the User model
    model = User

    # fields displayed in the user list view
    list_display = ('email', 'username', 'role', 'is_staff', 'is_active', 'email_verified', 'date_joined')

    # fields displayed in the right sidebar
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'email_verified', 'date_joined')

    # fields displayed from the top search bar
    search_fields = ('email', 'username', 'first_name', 'last_name')

    # default ordering in the list view (newest users first)
    ordering = ('-date_joined',)    

    # fields displayed in the user creation form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role and Avatar', {'fields': ('role', 'avatar')}),
    )

    # field groups shown when editing an existing user
    fieldsets = UserAdmin.fieldsets + (
        ('Role and Avatar', {'fields': ('role', 'avatar')}),
        ('Email Verification', {'fields': ('email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        ('Password Reset', {'fields': ('password_reset_token', 'password_reset_sent_at')}),
        ('Username Management', {'fields': ('username_updated_at',)}),
    )

    # fields that are read-only
    readonly_fields = ('date_joined', 'last_login', 'email_verification_token', 'password_reset_token')

