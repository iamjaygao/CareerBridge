from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import os

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
        return user

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
            
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,      
                "email": user.email,
                "role": user.role
            }
        }       

#----------------------------------------------------------
# User information Serializer (Read only)
# Used for profile display and update
#----------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar']    

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
        
            # File format check,the os.path.splitext(value.name)that split the file path into two parts
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
