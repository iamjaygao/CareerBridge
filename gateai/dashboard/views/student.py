from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get student dashboard statistics",
        responses={
            200: openapi.Response(
                description="Student dashboard data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "stats": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "upcomingAppointments": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "mentorSessions": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "resumesUploaded": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "profileViews": openapi.Schema(type=openapi.TYPE_INTEGER),
                            },
                            required=["upcomingAppointments", "mentorSessions", "resumesUploaded", "profileViews"],
                        ),
                        "activities": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_STRING),
                                    "type": openapi.Schema(type=openapi.TYPE_STRING),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING),
                                    "timestamp": openapi.Schema(type=openapi.TYPE_STRING),
                                },
                                required=["id", "type", "description", "timestamp"],
                            ),
                        ),
                    },
                    required=["stats", "activities"],
                ),
            ),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Dashboard not available for this role"),
        },
    )
    def get(self, request):
        user = request.user

        # 🔐 Role guard（必须）
        # 用 getattr 防御：避免某些测试/数据里 user 没 role 字段导致 AttributeError
        if getattr(user, "role", None) != "student":
            return Response(
                {"detail": "Dashboard not available for this role."},
                status=status.HTTP_403_FORBIDDEN,
            )

        stats = get_student_dashboard_stats(user)

        activities = [
            {
                "id": "1",
                "type": "appointment",
                "description": "You have an upcoming appointment",
                "timestamp": timezone.now().isoformat(),
            }
        ]

        return Response(
            {"stats": stats, "activities": activities},
            status=status.HTTP_200_OK,
        )


def get_student_dashboard_stats(user):
    # 延迟 import：减少循环依赖风险（你这么写是对的）
    from appointments.models import Appointment
    from ats_signals.models import Resume

    return {
        "upcomingAppointments": Appointment.objects.filter(
            user=user,
            status__in=["pending", "confirmed"],
        ).count(),
        "mentorSessions": Appointment.objects.filter(
            user=user,
            status="completed",
        ).count(),
        "resumesUploaded": Resume.objects.filter(user=user).count(),
        "profileViews": 0,
    }
