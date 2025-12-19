from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .serializers import ( RegisterSerializer,LoginSerializer, UserSerializer,
    UserUpdateSerializer, PasswordChangeSerializer,  ResendVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetSerializer)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.views import TokenRefreshView
from django.shortcuts import get_object_or_404
from .models import User

#----------------------------------------------------------
# Register View
# Handles user registration with email and password
#----------------------------------------------------------
print("🔥 USERS.VIEWS LOADED FROM:", __file__)


class RegisterView(APIView):
    # when a frontend sends a JSON request, DRF will automatically convert it to 
    # to a python dictionary before it reaches the post(self, request) method 
    # in the view.
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Registration failed")
        }
    )
    def post(self, request):
        from django.conf import settings

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # after this line the python dictionary is converted back to JSON automatically
            # and sent back to the frontend.
            is_development = getattr(settings, 'DEBUG', False)
            
            # Determine message based on user role and environment
            if user.role == 'admin':
                message = 'Admin user registered successfully. You can now log in immediately.'
            elif is_development:
                message = 'User registered successfully. In development mode, your account is automatically verified. You can log in immediately.'
            else:
                message = 'User registered successfully. Please check your email and click the verification link to activate your account. You must verify your email before you can log in.'
            
            return Response({
                'message': message
            }, status=status.HTTP_201_CREATED)
        
 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------------------
# Login View
# Handles user login with email and password
#----------------------------------------------------------
class LoginView(APIView):
    # The decorator swagger here is to generate documentation showing that 
    # This API expects a request body with fields that defined in the LoginSerializer.
    # It's for decumentation only, not for logic 
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(description="Login failed")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------------------
# Password Reset Request View
# Handles password reset request via email
#----------------------------------------------------------
class PasswordResetRequestView(APIView):
    @swagger_auto_schema(
        operation_description="Request password reset via email",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Password reset email sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Password reset request failed")
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password reset email sent successfully. Please check your email for the reset link.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------------------
# Password Reset View
# Handles password reset with token
#----------------------------------------------------------
class PasswordResetView(APIView):
    @swagger_auto_schema(
        operation_description="Reset password using reset token",
        request_body=PasswordResetSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Password reset failed")
        }
    )
    def post(self, request, token):
        serializer = PasswordResetSerializer(data={**request.data, 'token': token})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password reset successfully. You can now log in with your new password.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#----------------------------------------------------------
# Resend Verification Email View
# Handles resending verification emails
#----------------------------------------------------------
class ResendVerificationView(APIView):
    @swagger_auto_schema(
        operation_description="Resend verification email",
        request_body=ResendVerificationSerializer,
        responses={
            200: openapi.Response(
                description="Verification email sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Failed to send verification email")
        }
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Verification email sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#----------------------------------------------------------
# User View
# Handles user profile display and update
#----------------------------------------------------------
class UserView(APIView):
    #  Import the built-in permission class from DRF,which means 
    #  This API can only be accessed by authenticaed (logged in) users.
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user profile information",
        responses={
            200: UserSerializer,
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update current user profile information",
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Update failed"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def put(self,request):
        #UserUpdateSerializer(instance, data)
        # instance is the user object that we want to update
        serializer = UserUpdateSerializer(request.user, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'user profile updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------------------
# Username Change Status View
# Handles checking username modification status
#----------------------------------------------------------
class UsernameChangeStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check if user can change username and days remaining",
        responses={
            200: openapi.Response(
                description="Username change status",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'can_change': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'days_left': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        user = request.user
        can_change = True
        days_left = 0
        
        if user.username_updated_at:
            three_months_ago = timezone.now() - timedelta(days=90)
            if user.username_updated_at > three_months_ago:
                can_change = False
                delta = timezone.now() - user.username_updated_at
                days_left = (timedelta(days=90) - delta).days + 1
        
        return Response({
            'can_change': can_change,
            'days_left': days_left
        }, status=status.HTTP_200_OK)

#----------------------------------------------------------
# Password Change View
# Handles password updates with validation
#----------------------------------------------------------
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=PasswordChangeSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Password change failed"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data = request.data, context = {'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    
#----------------------------------------------------------
# Avatar Upload View
# Handles avatar uploads with validation
#----------------------------------------------------------
class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Upload user avatar image",
        manual_parameters=[
            openapi.Parameter(
                'avatar',
                openapi.IN_FORM,
                description="Avatar image file",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Avatar uploaded successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'avatar_url': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Upload failed")
        }
    )
    def post(self, request):
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response({'error': 'No avatar file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserUpdateSerializer(
            request.user,
            data={'avatar':avatar_file},
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message':'Avatar uploaded successfully',
                'avatar_url':request.user.avatar.url if request.user.avatar else None
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------------------
# JWT Refresh Token View
# Handles JWT token refresh
#----------------------------------------------------------
class RefreshTokenView(TokenRefreshView):
    @swagger_auto_schema(
        operation_description="Refresh JWT access token using refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
            },
            required=['refresh']
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Token refresh failed")
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

