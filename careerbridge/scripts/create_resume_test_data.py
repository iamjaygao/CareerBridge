#!/usr/bin/env python3
"""
Script to create test data for the resumes app
"""

import os
import sys
import django
from django.core.files.base import ContentFile
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from django.contrib.auth import get_user_model
from resumes.models import (
    Resume, ResumeAnalysis, ResumeFeedback, 
    ResumeTemplate, ResumeComparison
)
from resumes.services import ResumeAnalysisService

User = get_user_model()

def create_test_users():
    """Create test users if they don't exist"""
    users = []
    
    # Create test user 1
    user1, created = User.objects.get_or_create(
        username='testuser1',
        defaults={
            'email': 'testuser1@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'student'
        }
    )
    if created:
        user1.set_password('testpass123')
        user1.save()
        print(f"Created user: {user1.username}")
    users.append(user1)
    
    # Create test user 2
    user2, created = User.objects.get_or_create(
        username='testuser2',
        defaults={
            'email': 'testuser2@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'student'
        }
    )
    if created:
        user2.set_password('testpass123')
        user2.save()
        print(f"Created user: {user2.username}")
    users.append(user2)
    
    return users

def create_test_resumes(users):
    """Create test resumes for users"""
    resumes = []
    
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
        },
        {
            'title': 'Marketing Specialist Resume',
            'file_name': 'marketing_specialist_resume.pdf',
            'file_size': 41000,
            'file_type': 'pdf'
        }
    ]
    
    for i, user in enumerate(users):
        for j, data in enumerate(resume_data):
            resume, created = Resume.objects.get_or_create(
                user=user,
                title=f"{data['title']} - {user.username}",
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
            
            resumes.append(resume)
    
    return resumes

def create_test_analyses(resumes):
    """Create test analyses for resumes"""
    analyses = []
    
    for resume in resumes:
        # Skip if already analyzed
        if resume.has_analysis:
            continue
        
        try:
            # Use the service to create analysis
            analysis = ResumeAnalysisService.analyze_resume(
                resume.id,
                industry='technology' if 'Software' in resume.title else 'general',
                job_title='Software Engineer' if 'Software' in resume.title else 'Professional'
            )
            analyses.append(analysis)
            print(f"Created analysis for: {resume.title}")
            
        except Exception as e:
            print(f"Error creating analysis for {resume.title}: {e}")
    
    return analyses

def create_test_templates():
    """Create test resume templates"""
    templates = []
    
    template_data = [
        {
            'name': 'Modern Professional',
            'description': 'Clean and modern template suitable for all industries',
            'template_type': 'modern',
            'industry': 'general',
            'html_template': '<div class="modern-template">...</div>',
            'css_styles': '.modern-template { font-family: Arial, sans-serif; }',
            'is_premium': False
        },
        {
            'name': 'Classic Executive',
            'description': 'Traditional template for senior professionals',
            'template_type': 'classic',
            'industry': 'general',
            'html_template': '<div class="classic-template">...</div>',
            'css_styles': '.classic-template { font-family: Times New Roman, serif; }',
            'is_premium': True
        },
        {
            'name': 'Tech Startup',
            'description': 'Creative template for technology professionals',
            'template_type': 'creative',
            'industry': 'technology',
            'html_template': '<div class="tech-template">...</div>',
            'css_styles': '.tech-template { font-family: "Courier New", monospace; }',
            'is_premium': False
        },
        {
            'name': 'Finance Professional',
            'description': 'Conservative template for finance industry',
            'template_type': 'professional',
            'industry': 'finance',
            'html_template': '<div class="finance-template">...</div>',
            'css_styles': '.finance-template { font-family: Georgia, serif; }',
            'is_premium': True
        }
    ]
    
    for data in template_data:
        template, created = ResumeTemplate.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if created:
            print(f"Created template: {template.name}")
        templates.append(template)
    
    return templates

def create_test_comparisons(users, resumes):
    """Create test resume comparisons"""
    comparisons = []
    
    # Group resumes by user
    user_resumes = {}
    for resume in resumes:
        if resume.user not in user_resumes:
            user_resumes[resume.user] = []
        user_resumes[resume.user].append(resume)
    
    for user, user_resume_list in user_resumes.items():
        if len(user_resume_list) >= 2:
            # Create comparison between first two resumes
            original = user_resume_list[0]
            improved = user_resume_list[1]
            
            # Ensure both have analysis
            if not original.has_analysis:
                try:
                    ResumeAnalysisService.analyze_resume(original.id)
                except:
                    continue
            
            if not improved.has_analysis:
                try:
                    ResumeAnalysisService.analyze_resume(improved.id)
                except:
                    continue
            
            comparison, created = ResumeComparison.objects.get_or_create(
                user=user,
                title=f"Comparison: {original.title} vs {improved.title}",
                defaults={
                    'description': f"Comparison between original and improved versions",
                    'original_resume': original,
                    'improved_resume': improved,
                    'score_improvement': Decimal('5.50'),
                    'improvement_areas': ['keyword_optimization', 'structure_improvement'],
                    'maintained_strengths': ['technical_skills', 'experience_level']
                }
            )
            
            if created:
                print(f"Created comparison: {comparison.title}")
            comparisons.append(comparison)
    
    return comparisons

def main():
    """Main function to create all test data"""
    print("Creating test data for resumes app...")
    
    # Create users
    print("\n1. Creating test users...")
    users = create_test_users()
    
    # Create resumes
    print("\n2. Creating test resumes...")
    resumes = create_test_resumes(users)
    
    # Create analyses
    print("\n3. Creating test analyses...")
    analyses = create_test_analyses(resumes)
    
    # Create templates
    print("\n4. Creating test templates...")
    templates = create_test_templates()
    
    # Create comparisons
    print("\n5. Creating test comparisons...")
    comparisons = create_test_comparisons(users, resumes)
    
    # Summary
    print("\n" + "="*50)
    print("Test data creation completed!")
    print(f"Users created: {len(users)}")
    print(f"Resumes created: {len(resumes)}")
    print(f"Analyses created: {len(analyses)}")
    print(f"Templates created: {len(templates)}")
    print(f"Comparisons created: {len(comparisons)}")
    print("="*50)
    
    # Print sample data for testing
    print("\nSample data for testing:")
    if users:
        print(f"Test user: {users[0].username} (password: testpass123)")
    if resumes:
        print(f"Sample resume ID: {resumes[0].id}")
    if templates:
        print(f"Sample template ID: {templates[0].id}")

if __name__ == '__main__':
    main() 