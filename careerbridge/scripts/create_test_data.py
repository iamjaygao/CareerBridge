#!/usr/bin/env python3
"""
Script to create test data for CareerBridge mentors
"""

import os
import sys
import django
from datetime import date, time, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from django.contrib.auth import get_user_model
from mentors.models import (
    MentorProfile, MentorService, MentorAvailability, 
    MentorSession, MentorReview, MentorApplication
)

User = get_user_model()

def create_test_users():
    """Create test users"""
    users = []
    
    # Create mentor users
    mentor_data = [
        {
            'username': 'john_mentor',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'role': 'mentor'
        },
        {
            'username': 'sarah_mentor',
            'email': 'sarah@example.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'mentor'
        },
        {
            'username': 'mike_mentor',
            'email': 'mike@example.com',
            'first_name': 'Mike',
            'last_name': 'Davis',
            'role': 'mentor'
        }
    ]
    
    for data in mentor_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role']
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"Created user: {user.username}")
        users.append(user)
    
    # Create student users
    student_data = [
        {
            'username': 'alice_student',
            'email': 'alice@example.com',
            'first_name': 'Alice',
            'last_name': 'Brown',
            'role': 'student'
        },
        {
            'username': 'bob_student',
            'email': 'bob@example.com',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'role': 'student'
        }
    ]
    
    for data in student_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role']
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"Created user: {user.username}")
        users.append(user)
    
    return users

def create_mentor_profiles(mentor_users):
    """Create mentor profiles"""
    profiles = []
    
    profile_data = [
        {
            'user': mentor_users[0],
            'bio': 'Senior Software Engineer with 8+ years of experience in full-stack development. Passionate about helping others grow in their careers.',
            'years_of_experience': 8,
            'current_position': 'Senior Software Engineer at TechCorp',
            'industry': 'Technology',
            'status': 'approved',
            'average_rating': Decimal('4.8'),
            'total_reviews': 15,
            'total_sessions': 25,
            'total_earnings': Decimal('1250.00'),
            'is_verified': True,
            'verification_badge': 'verified_expert',
            'specializations': ['resume_review', 'mock_interview', 'career_consultation']
        },
        {
            'user': mentor_users[1],
            'bio': 'Product Manager with expertise in product strategy and user experience. Helped 50+ professionals transition into product roles.',
            'years_of_experience': 6,
            'current_position': 'Product Manager at StartupXYZ',
            'industry': 'Technology',
            'status': 'approved',
            'average_rating': Decimal('4.9'),
            'total_reviews': 22,
            'total_sessions': 35,
            'total_earnings': Decimal('2100.00'),
            'is_verified': True,
            'verification_badge': 'verified_expert',
            'specializations': ['career_consultation', 'mock_interview']
        },
        {
            'user': mentor_users[2],
            'bio': 'Data Scientist with strong background in machine learning and analytics. Expert in helping data professionals advance their careers.',
            'years_of_experience': 5,
            'current_position': 'Lead Data Scientist at DataCorp',
            'industry': 'Technology',
            'status': 'approved',
            'average_rating': Decimal('4.7'),
            'total_reviews': 12,
            'total_sessions': 18,
            'total_earnings': Decimal('900.00'),
            'is_verified': True,
            'verification_badge': 'verified_expert',
            'specializations': ['resume_review', 'career_consultation']
        }
    ]
    
    for data in profile_data:
        profile, created = MentorProfile.objects.get_or_create(
            user=data['user'],
            defaults=data
        )
        if created:
            print(f"Created mentor profile: {profile.user.username}")
        profiles.append(profile)
    
    return profiles

def create_mentor_services(profiles):
    """Create mentor services"""
    services = []
    
    service_data = [
        {
            'mentor': profiles[0],
            'service_type': 'resume_review',
            'title': 'Comprehensive Resume Review',
            'description': 'Get detailed feedback on your resume structure, content, and ATS optimization.',
            'pricing_model': 'fixed',
            'fixed_price': Decimal('75.00'),
            'duration_minutes': 60
        },
        {
            'mentor': profiles[0],
            'service_type': 'mock_interview',
            'title': 'Technical Interview Practice',
            'description': 'Practice coding problems and system design questions with real-time feedback.',
            'pricing_model': 'hourly',
            'price_per_hour': Decimal('100.00'),
            'duration_minutes': 90
        },
        {
            'mentor': profiles[1],
            'service_type': 'career_consultation',
            'title': 'Career Strategy Session',
            'description': 'Plan your career transition and develop a roadmap for achieving your goals.',
            'pricing_model': 'hourly',
            'price_per_hour': Decimal('120.00'),
            'duration_minutes': 60
        },
        {
            'mentor': profiles[2],
            'service_type': 'resume_review',
            'title': 'Data Science Resume Review',
            'description': 'Specialized resume review for data science and analytics professionals.',
            'pricing_model': 'fixed',
            'fixed_price': Decimal('85.00'),
            'duration_minutes': 60
        }
    ]
    
    for data in service_data:
        service, created = MentorService.objects.get_or_create(
            mentor=data['mentor'],
            service_type=data['service_type'],
            defaults=data
        )
        if created:
            print(f"Created service: {service.title} for {service.mentor.user.username}")
        services.append(service)
    
    return services

def create_mentor_availability(profiles):
    """Create mentor availability"""
    availability_data = []
    
    # Create availability for each mentor
    for profile in profiles:
        # Monday to Friday, 9 AM to 5 PM
        for day in range(5):  # Monday to Friday
            availability_data.append({
                'mentor': profile,
                'day_of_week': day,
                'start_time': time(9, 0),  # 9:00 AM
                'end_time': time(17, 0),   # 5:00 PM
                'is_active': True
            })
    
    for data in availability_data:
        availability, created = MentorAvailability.objects.get_or_create(
            mentor=data['mentor'],
            day_of_week=data['day_of_week'],
            start_time=data['start_time'],
            defaults=data
        )
        if created:
            print(f"Created availability for {availability.mentor.user.username} on day {availability.day_of_week}")

def create_test_sessions(profiles, services, student_users):
    """Create some test sessions"""
    from datetime import datetime, timedelta
    
    # Create a few completed sessions
    session_data = [
        {
            'mentor': profiles[0],
            'user': student_users[0],
            'service': services[0],
            'scheduled_date': date.today() - timedelta(days=7),
            'scheduled_time': time(14, 0),
            'status': 'completed',
            'user_notes': 'Need help with resume optimization for software engineering roles'
        },
        {
            'mentor': profiles[1],
            'user': student_users[1],
            'service': services[2],
            'scheduled_date': date.today() - timedelta(days=3),
            'scheduled_time': time(10, 0),
            'status': 'completed',
            'user_notes': 'Want to transition from marketing to product management'
        }
    ]
    
    for data in session_data:
        session, created = MentorSession.objects.get_or_create(
            mentor=data['mentor'],
            user=data['user'],
            service=data['service'],
            scheduled_date=data['scheduled_date'],
            defaults=data
        )
        if created:
            print(f"Created session: {session.mentor.user.username} with {session.user.username}")

def create_test_reviews(profiles, student_users):
    """Create some test reviews"""
    review_data = [
        {
            'mentor': profiles[0],
            'user': student_users[0],
            'rating': 5,
            'comment': 'Excellent resume review! John provided detailed feedback that helped me land interviews.'
        },
        {
            'mentor': profiles[1],
            'user': student_users[1],
            'rating': 5,
            'comment': 'Sarah gave me great career advice and helped me create a clear roadmap for my transition.'
        }
    ]
    
    for data in review_data:
        review, created = MentorReview.objects.get_or_create(
            mentor=data['mentor'],
            user=data['user'],
            defaults=data
        )
        if created:
            print(f"Created review: {review.rating} stars from {review.user.username}")

def main():
    """Main function to create all test data"""
    print("Creating test data for CareerBridge...")
    
    # Create users
    users = create_test_users()
    mentor_users = [u for u in users if u.role == 'mentor']
    student_users = [u for u in users if u.role == 'student']
    
    # Create mentor profiles
    profiles = create_mentor_profiles(mentor_users)
    
    # Create services
    services = create_mentor_services(profiles)
    
    # Create availability
    create_mentor_availability(profiles)
    
    # Create test sessions
    create_test_sessions(profiles, services, student_users)
    
    # Create test reviews
    create_test_reviews(profiles, student_users)
    
    print("\n✅ Test data creation completed!")
    print(f"Created {len(mentor_users)} mentors and {len(student_users)} students")
    print(f"Created {len(profiles)} mentor profiles")
    print(f"Created {len(services)} services")
    print("\nYou can now test the APIs with this data!")

if __name__ == "__main__":
    main() 