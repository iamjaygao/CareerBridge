from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import os
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import uuid

User = get_user_model()

#----------------------------------------------------------
# Register serializer
# save the data to the database, that is the reason we need to use ModelSerializer.
#----------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'role']

    # ensure both passwords match
    def validate(self, attrs):   
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs
    
    def validate_email(self, value):
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
    def validate_username(self, value):
        # Check if username already exists
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def create(self, validated_data):
        # remove password_confirm from validated data
        validated_data.pop('password_confirm')

        # Create user with default role if not provided
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', 'student')
        )
        
        # Send email verification
        self.send_verification_email(user)
        
        return user
    
    def send_verification_email(self, user):
        """Send email verification email"""
        verification_url = f"http://localhost:8000/api/v1/users/verify-email/{user.email_verification_token}/"
        
        subject = 'CareerBridge - Email Verification'
        message = f"""
        Welcome to CareerBridge!
        
        Please click the following link to verify your email:
        {verification_url}
        
        If you did not register for CareerBridge, please ignore this email.
        
        This link is valid for 24 hours.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            user.email_verification_sent_at = timezone.now()
            user.save()
        except Exception as e:
            # In development environment, email sending failure won't prevent user registration
            print(f"Email sending failed: {e}")

#----------------------------------------------------------
# Login serializer
# Authenticate using username or email and returns access and refresh tokens.
#----------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login_input = attrs.get("login")
        password = attrs.get("password")

        user = authenticate(username=login_input, password=password)
        if not user:
            raise serializers.ValidationError("The username or password is incorrect")
        
        # Check if email is verified - required for login
        if not user.email_verified:
            raise serializers.ValidationError("Please verify your email before logging in. Check your email for the verification link.")
            
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,      
                "email": user.email,
                "role": user.role,
                "email_verified": user.email_verified
            }
        }       

#----------------------------------------------------------
# Email verification serializer
# Handles email verification
#----------------------------------------------------------
class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        try:
            user = User.objects.get(email_verification_token=value)
            # Check if token is expired (24 hours)
            if user.email_verification_sent_at:
                token_age = timezone.now() - user.email_verification_sent_at
                if token_age > timedelta(hours=24):
                    raise serializers.ValidationError("Verification link has expired. Please request a new one.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")
        return value
    
    def save(self):
        token = self.validated_data['token']
        user = User.objects.get(email_verification_token=token)
        user.email_verified = True
        user.save()
        return user

#----------------------------------------------------------
# Resend verification email serializer
# Handles resending verification emails
#----------------------------------------------------------
class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.email_verified:
                raise serializers.ValidationError("Email is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value
    
    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate new token
        user.email_verification_token = uuid.uuid4()
        user.save()
        
        # Send new verification email
        self.send_verification_email(user)
        return user
    
    def send_verification_email(self, user):
        """Send email verification email"""
        verification_url = f"http://localhost:8000/api/v1/users/verify-email/{user.email_verification_token}/"
        
        subject = 'CareerBridge - Email Verification'
        message = f"""
        You requested to resend the email verification.
        
        Please click the following link to verify your email:
        {verification_url}
        
        If you did not request this email, please ignore it.
        
        This link is valid for 24 hours.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            user.email_verification_sent_at = timezone.now()
            user.save()
        except Exception as e:
            print(f"Email sending failed: {e}")

#----------------------------------------------------------
# User information Serializer (Read only)
# Used for profile display and update
#----------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar', 'email_verified']    

#----------------------------------------------------------
# Update user serializer    
# Handles username, email, avatar updates with constraints
#----------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']
    
    def validate_avatar(self, value):
        if value:
            # File size check (5MB max)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("File size exceeds 5MB limit")
        
            # File format check - os.path.splitext(value.name) splits the file path into two parts:
            # the first part is the file name, the second part is the file extension including the dot.
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            extension = os.path.splitext(value.name)[1].lower()
            if extension not in allowed_extensions:
                raise serializers.ValidationError("Unsupported file format. Please upload a JPG, JPEG, PNG, or GIF file.")
        
            # Filename length check
            if len(value.name) > 100:
                raise serializers.ValidationError("Filename is too long. Please use a shorter name.")
        return value

    def validate_username(self, value):
        user = self.context['request'].user

        # if the new username sent by the frontend is different from the current name
        if user.username != value:

            # check if username already exists (exclude current user)
            if User.objects.filter(username=value).exclude(id=user.id).exists():
                raise serializers.ValidationError("This username is already taken")

            # Enforce 3-month limit on changing username    
            # DataTimeField in the User model is used to store the last time of the username change.
            # In Python, the if statement will run the block if the value is not empty, not None, not false
            # and it will skip if the value is None, False or empty string.

            if user.username_updated_at:
                three_months_ago = timezone.now() - timedelta(days=90)
                if user.username_updated_at > three_months_ago:
                    delta = timezone.now() - user.username_updated_at
                    delta_left = (timedelta(days=90) - delta).days + 1
                    raise serializers.ValidationError(f"You can only change your username once every 3 months. Please try again in {delta_left} days.")
        return value
    
    def validate_email(self, value):
        user = self.context['request'].user
        if user.email != value:
            if User.objects.filter(email=value).exclude(id=user.id).exists():
                raise serializers.ValidationError("This email is already in use")
        return value
    
    def update(self, instance, validated_data):
        # Update the username_updated_at timestamp if username is changed
        if 'username' in validated_data and validated_data['username'] != instance.username:
            validated_data['username_updated_at'] = timezone.now()

        # look through the validated_data (each field in the user model) assign the value to the instance 
        # and save it to the database
        # super() is used to call the update method of the parent class (ModelSerializer)
        return super().update(instance, validated_data)

#----------------------------------------------------------
# Password reset request serializer
# Handles password reset request via email
#----------------------------------------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.email_verified:
                raise serializers.ValidationError("This email is not verified. Please verify your email first.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value
    
    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate password reset token
        user.password_reset_token = uuid.uuid4()
        user.password_reset_sent_at = timezone.now()
        user.save()
        
        # Send password reset email
        self.send_password_reset_email(user)
        return user
    
    def send_password_reset_email(self, user):
        """Send password reset email"""
        reset_url = f"http://localhost:8000/api/v1/users/reset-password/{user.password_reset_token}/"
        
        subject = 'CareerBridge - Password Reset'
        message = f"""
        You requested a password reset for your CareerBridge account.
        
        Please click the following link to reset your password:
        {reset_url}
        
        If you did not request this password reset, please ignore this email.
        
        This link is valid for 1 hour.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Password reset email sending failed: {e}")

#----------------------------------------------------------
# Password reset serializer
# Handles password reset with token
#----------------------------------------------------------
class PasswordResetSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_token(self, value):
        try:
            user = User.objects.get(password_reset_token=value)
            # Check if token is expired (1 hour)
            if user.password_reset_sent_at:
                token_age = timezone.now() - user.password_reset_sent_at
                if token_age > timedelta(hours=1):
                    raise serializers.ValidationError("Password reset link has expired. Please request a new one.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid password reset token.")
        return value
    
    def validate_new_password(self, value):
        # Use django's built-in password validator
        validate_password(value)
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("The new passwords do not match")
        return attrs
    
    def save(self):
        token = self.validated_data['token']
        user = User.objects.get(password_reset_token=token)
        user.set_password(self.validated_data['new_password'])
        user.password_reset_token = None  # Clear the token
        user.password_reset_sent_at = None
        user.save()
        return user

#----------------------------------------------------------
# Username recovery serializer
# Handles username recovery via email
#----------------------------------------------------------
class UsernameRecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.email_verified:
                raise serializers.ValidationError("This email is not verified. Please verify your email first.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value
    
    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Send username recovery email
        self.send_username_recovery_email(user)
        return user
    
    def send_username_recovery_email(self, user):
        """Send username recovery email"""
        subject = 'CareerBridge - Username Recovery'
        message = f"""
        You requested to recover your username for your CareerBridge account.
        
        Your username is: {user.username}
        
        If you did not request this username recovery, please ignore this email.
        
        For security reasons, please keep your username private.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Username recovery email sending failed: {e}")

#----------------------------------------------------------
# Password change serializer
# Handles password updates with validation
#----------------------------------------------------------
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("The old password is incorrect")
        return value

    def validate_new_password(self, value):
        # Use django's built-in password validator
        validate_password(value)
        return value

    # the validate is a built-in method in the Serializer class, we override it to add custom validation
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("The new passwords do not match")
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
