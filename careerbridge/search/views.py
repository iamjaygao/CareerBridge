from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from collections import Counter
import json
from typing import Dict, List

@api_view(['GET'])
def popular_jobs(request):
    """Get popular job titles from actual job data"""
    try:
        # Try JobListing model first
        try:
            from jobs.models import JobListing
            popular = JobListing.objects.filter(
                is_active=True
            ).values('title').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            jobs = [item['title'] for item in popular if item['title']]
            if jobs:
                return Response(jobs)
        except ImportError:
            pass
        
        # Fallback to JobDescription model
        try:
            from resumes.models import JobDescription
            popular = JobDescription.objects.values('title').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            jobs = [item['title'] for item in popular if item['title']]
            if jobs:
                return Response(jobs)
        except ImportError:
            pass
        
        # If no job data exists, return empty array
        return Response([])
        
    except Exception as e:
        # Log error but return empty array to prevent frontend crashes
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching popular jobs: {e}")
        return Response([])

@api_view(['GET'])
def popular_skills(request):
    """Get popular skills from resume and job data"""
    try:
        all_skills = []
        
        # Extract skills from JobDescription model
        try:
            from resumes.models import JobDescription
            job_descriptions = JobDescription.objects.filter(
                Q(required_skills__isnull=False) | Q(preferred_skills__isnull=False)
            ).values('required_skills', 'preferred_skills')
            
            for job in job_descriptions:
                if job.get('required_skills'):
                    if isinstance(job['required_skills'], list):
                        all_skills.extend(job['required_skills'])
                    elif isinstance(job['required_skills'], str):
                        try:
                            skills_list = json.loads(job['required_skills'])
                            if isinstance(skills_list, list):
                                all_skills.extend(skills_list)
                        except:
                            pass
                
                if job.get('preferred_skills'):
                    if isinstance(job['preferred_skills'], list):
                        all_skills.extend(job['preferred_skills'])
                    elif isinstance(job['preferred_skills'], str):
                        try:
                            skills_list = json.loads(job['preferred_skills'])
                            if isinstance(skills_list, list):
                                all_skills.extend(skills_list)
                        except:
                            pass
        except ImportError:
            pass
        
        # Extract skills from ResumeAnalysis model
        try:
            from resumes.models import ResumeAnalysis
            resume_analyses = ResumeAnalysis.objects.filter(
                Q(technical_skills__isnull=False) | Q(soft_skills__isnull=False)
            ).values('technical_skills', 'soft_skills')
            
            for analysis in resume_analyses:
                if analysis.get('technical_skills'):
                    if isinstance(analysis['technical_skills'], list):
                        all_skills.extend(analysis['technical_skills'])
                    elif isinstance(analysis['technical_skills'], str):
                        try:
                            skills_list = json.loads(analysis['technical_skills'])
                            if isinstance(skills_list, list):
                                all_skills.extend(skills_list)
                        except:
                            pass
                
                if analysis.get('soft_skills'):
                    if isinstance(analysis['soft_skills'], list):
                        all_skills.extend(analysis['soft_skills'])
                    elif isinstance(analysis['soft_skills'], str):
                        try:
                            skills_list = json.loads(analysis['soft_skills'])
                            if isinstance(skills_list, list):
                                all_skills.extend(skills_list)
                        except:
                            pass
        except ImportError:
            pass
        
        # Count and return top skills
        if all_skills:
            # Normalize skills (strip whitespace, handle case)
            normalized_skills = [str(skill).strip() for skill in all_skills if skill]
            skill_counts = Counter(normalized_skills)
            popular = [skill for skill, count in skill_counts.most_common(10)]
            return Response(popular)
        
        # If no skill data exists, return empty array
        return Response([])
        
    except Exception as e:
        # Log error but return empty array to prevent frontend crashes
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching popular skills: {e}")
        return Response([])

@api_view(['GET'])
def popular_industries(request):
    """Get popular industries from job data"""
    try:
        # Try JobListing model first
        try:
            from jobs.models import JobListing
            if hasattr(JobListing, 'industry'):
                popular = JobListing.objects.filter(
                    is_active=True,
                    industry__isnull=False
                ).exclude(industry='').values('industry').annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
                
                industries = [item['industry'] for item in popular if item['industry']]
                if industries:
                    return Response(industries)
        except (ImportError, AttributeError):
            pass
        
        # Fallback: extract industries from company names or other fields
        # This is a placeholder - adjust based on actual model structure
        try:
            from resumes.models import JobDescription
            # If JobDescription has an industry field, use it
            if hasattr(JobDescription, 'industry'):
                popular = JobDescription.objects.filter(
                    industry__isnull=False
                ).exclude(industry='').values('industry').annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
                
                industries = [item['industry'] for item in popular if item['industry']]
                if industries:
                    return Response(industries)
        except (ImportError, AttributeError):
            pass
        
        # If no industry data exists, return empty array
        return Response([])
        
    except Exception as e:
        # Log error but return empty array to prevent frontend crashes
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching popular industries: {e}")
        return Response([])


@api_view(['GET'])
def search_all(request):
    """Lightweight unified search endpoint"""
    query = (request.GET.get('q') or '').strip()
    if not query:
        return Response({'jobs': [], 'mentors': [], 'resumes': []})

    results: Dict[str, List] = {'jobs': [], 'mentors': [], 'resumes': []}

    try:
        from mentors.models import MentorProfile
        mentors = MentorProfile.objects.filter(
            Q(status='approved'),
            Q(user__username__icontains=query)
            | Q(current_position__icontains=query)
            | Q(industry__icontains=query)
            | Q(headline__icontains=query)
        ).select_related('user')[:10]
        results['mentors'] = [
            {
                'id': mentor.id,
                'name': mentor.user.get_full_name() or mentor.user.username,
                'headline': mentor.headline or mentor.current_position,
                'industry': mentor.industry,
            }
            for mentor in mentors
        ]
    except Exception:
        results['mentors'] = []

    try:
        from resumes.models import Resume
        resumes = Resume.objects.filter(
            Q(title__icontains=query),
        ).select_related('user')[:10]
        results['resumes'] = [
            {
                'id': resume.id,
                'title': resume.title,
                'user_id': resume.user_id,
            }
            for resume in resumes
        ]
    except Exception:
        results['resumes'] = []

    return Response(results)


@api_view(['GET'])
def search_suggestions(request):
    """Return lightweight suggestions across jobs/skills/industries"""
    query = (request.GET.get('q') or '').strip().lower()
    limit = int(request.GET.get('limit') or 10)

    if not query:
        return Response([])

    suggestions = []

    try:
        jobs = popular_jobs(request).data or []
        for job in jobs:
            if query in str(job).lower():
                suggestions.append({
                    'id': f'job:{job}',
                    'text': job,
                    'type': 'job_title',
                    'relevance': 0.9,
                })
    except Exception:
        pass

    try:
        skills = popular_skills(request).data or []
        for skill in skills:
            if query in str(skill).lower():
                suggestions.append({
                    'id': f'skill:{skill}',
                    'text': skill,
                    'type': 'skill',
                    'relevance': 0.8,
                })
    except Exception:
        pass

    try:
        industries = popular_industries(request).data or []
        for industry in industries:
            if query in str(industry).lower():
                suggestions.append({
                    'id': f'industry:{industry}',
                    'text': industry,
                    'type': 'industry',
                    'relevance': 0.7,
                })
    except Exception:
        pass

    return Response(suggestions[:limit])


@api_view(['GET'])
def trending_searches(request):
    """Return trending search terms (fallback to popular data)"""
    limit = int(request.GET.get('limit') or 10)
    trending = []

    try:
        jobs = popular_jobs(request).data or []
        trending.extend([
            {
                'id': f'job:{job}',
                'text': job,
                'type': 'job_title',
                'relevance': 0.9,
            }
            for job in jobs
        ])
    except Exception:
        pass

    return Response(trending[:limit])


@api_view(['GET'])
def search_filters(request):
    """Return available filter options for search UI"""
    return Response({
        'types': [],
        'industries': [],
        'skills': [],
        'locations': [],
        'experience_levels': [],
        'price_ranges': [],
        'availability': [],
    })


@api_view(['GET', 'POST', 'DELETE'])
def search_history(request):
    """Placeholder search history endpoint"""
    if request.method == 'GET':
        return Response([])
    return Response({'status': 'ok'})


@api_view(['GET'])
def search_analytics(request):
    """Placeholder search analytics endpoint"""
    return Response({
        'total_searches': 0,
        'popular_queries': [],
        'search_trends': [],
        'no_results_queries': [],
    })
