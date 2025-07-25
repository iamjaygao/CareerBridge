from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . serializers import RegisterSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterView(APIView):
    # when a frontend sends a JSON request, DRF will automatically convert it to 
    # to a python dictionary before it reaches the post(self, request) method 
    # in the view.
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            # after this line the python dictionary is converted back to JSON automatically
            # and sent back to the frontend.
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)