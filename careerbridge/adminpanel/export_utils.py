import csv
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q


def build_export_rows(export_type, filters, date_from=None, date_to=None):
    if export_type == 'users':
        User = get_user_model()
        queryset = User.objects.all()
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(username__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term)
            )
        if 'is_active' in filters:
            queryset = queryset.filter(is_active=bool(filters['is_active']))
        if filters.get('role'):
            queryset = queryset.filter(role=filters['role'])
        if 'is_staff' in filters:
            queryset = queryset.filter(is_staff=bool(filters['is_staff']))
        if filters.get('exclude_admin'):
            queryset = queryset.exclude(role='admin').exclude(role='staff')

        rows = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': getattr(user, 'role', '') or 'student',
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.isoformat() if user.date_joined else '',
                'last_login': user.last_login.isoformat() if user.last_login else '',
            }
            for user in queryset.order_by('id')
        ]
        return rows

    if export_type == 'mentors':
        from mentors.models import MentorProfile

        queryset = MentorProfile.objects.select_related('user').all()
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        rows = [
            {
                'mentor_id': mentor.id,
                'user_id': mentor.user.id if mentor.user else '',
                'username': mentor.user.username if mentor.user else '',
                'email': mentor.user.email if mentor.user else '',
                'status': mentor.status,
                'average_rating': mentor.average_rating,
                'total_reviews': mentor.total_reviews,
                'total_sessions': mentor.total_sessions,
                'total_earnings': mentor.total_earnings,
            }
            for mentor in queryset.order_by('id')
        ]
        return rows

    if export_type == 'appointments':
        from appointments.models import Appointment

        queryset = Appointment.objects.select_related('user', 'mentor__user').all()
        if date_from:
            queryset = queryset.filter(scheduled_start__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(scheduled_start__date__lte=date_to)
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        if 'is_paid' in filters:
            queryset = queryset.filter(is_paid=bool(filters['is_paid']))

        rows = [
            {
                'appointment_id': appointment.id,
                'student_username': appointment.user.username if appointment.user else '',
                'student_email': appointment.user.email if appointment.user else '',
                'mentor_username': appointment.mentor.user.username if appointment.mentor else '',
                'mentor_email': appointment.mentor.user.email if appointment.mentor else '',
                'status': appointment.status,
                'scheduled_start': appointment.scheduled_start.isoformat() if appointment.scheduled_start else '',
                'price': appointment.price,
                'is_paid': appointment.is_paid,
            }
            for appointment in queryset.order_by('id')
        ]
        return rows

    return []


def write_export_file(export_type, rows, export_id):
    export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
    os.makedirs(export_dir, exist_ok=True)
    filename = f"export_{export_id}_{export_type}.csv"
    file_path = os.path.join(export_dir, filename)

    if rows:
        headers = list(rows[0].keys())
    else:
        headers = []

    with open(file_path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        if headers:
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row.get(key, '') for key in headers])

    return file_path, os.path.getsize(file_path)
