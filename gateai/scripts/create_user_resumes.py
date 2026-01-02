#!/usr/bin/env python3
"""
Script to create resumes for the verified user
"""

import os
import sys
import django
from django.core.files.base import ContentFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')
django.setup()

from django.contrib.auth import get_user_model
from ats_signals.models import Resume
from ats_signals.services import ResumeAnalysisService

User = get_user_model()

def create_user_resumes():
    """Create resumes for verified_user"""
    username = 'verified_user'
    
    try:
        user = User.objects.get(username=username)
        print(f"Found user: {username}")
    except User.DoesNotExist:
        print(f"User {username} not found")
        return
    
    # Sample resume data
    resume_data = [
        {
            'title': 'Software Engineer Resume',
            'file_name': 'software_engineer_resume.pdf',
            'file_size': 45000,
            'file_type': 'pdf'
        },
        {
            'title': 'Data Scientist Resume',
            'file_name': 'data_scientist_resume.pdf',
            'file_size': 52000,
            'file_type': 'pdf'
        },
        {
            'title': 'Product Manager Resume',
            'file_name': 'product_manager_resume.pdf',
            'file_size': 38000,
            'file_type': 'pdf'
        }
    ]
    
    resumes = []
    for data in resume_data:
        resume, created = Resume.objects.get_or_create(
            user=user,
            title=data['title'],
            defaults={
                'file_size': data['file_size'],
                'file_type': data['file_type'],
                'status': 'uploaded'
            }
        )
        
        if created:
            # Create a mock PDF file content
            mock_pdf_content = f"Mock PDF content for {data['title']} by {user.username}"
            resume.file.save(
                data['file_name'],
                ContentFile(mock_pdf_content.encode('utf-8'))
            )
            resume.save()
            print(f"Created resume: {resume.title}")
        else:
            print(f"Resume already exists: {resume.title}")
        
        resumes.append(resume)
    
    # Create analyses for resumes
    print("\nCreating analyses...")
    for resume in resumes:
        if not resume.has_analysis:
            try:
                analysis = ResumeAnalysisService.analyze_resume(
                    resume.id,
                    industry='technology' if 'Software' in resume.title else 'general',
                    job_title='Software Engineer' if 'Software' in resume.title else 'Professional'
                )
                print(f"Created analysis for: {resume.title}")
            except Exception as e:
                print(f"Error creating analysis for {resume.title}: {e}")
        else:
            print(f"Analysis already exists for: {resume.title}")
    
    print(f"\nCreated {len(resumes)} resumes for {username}")
    print("Resume IDs:", [r.id for r in resumes])

if __name__ == '__main__':
    create_user_resumes() 