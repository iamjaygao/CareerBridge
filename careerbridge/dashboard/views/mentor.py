from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from dashboard.services.mentor_stats import get_mentor_dashboard_stats


class MentorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Get mentor dashboard")
    def get(self, request):
        user = request.user

        if user.role != "mentor":
            return Response(
                {"detail": "Dashboard not available for this role."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "stats": get_mentor_dashboard_stats(user),
                "activities": [],
            },
            status=status.HTTP_200_OK,
        )
