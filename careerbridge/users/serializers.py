from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from . models import User

# Register serializer
# save the data to the datebase,that is the reason we need to use ModelSerializer.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm','role']

    # ensure both passwords match
    def validate(self, attrs):   
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs
    
    def create(self, validated_data):
        #remve confirm password from validated data
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role','student')
        )
        return user
    
# Login serializer
# only returns the access token and refresh token, not the user data.
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

# User serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role','avatar']    