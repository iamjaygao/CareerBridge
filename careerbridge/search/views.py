from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from resumes.models import Resume
from mentors.models import MentorProfile
import random

@api_view(['GET'])
def popular_jobs(request):
    """获取热门工作列表"""
    # 模拟热门工作数据
    popular_jobs = [
        "Software Engineer",
        "Data Scientist", 
        "Product Manager",
        "UX Designer",
        "DevOps Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Machine Learning Engineer",
        "Cloud Architect"
    ]
    return Response(popular_jobs)

@api_view(['GET'])
def popular_skills(request):
    """获取热门技能列表"""
    # 模拟热门技能数据
    popular_skills = [
        "Python",
        "JavaScript",
        "React",
        "Node.js",
        "AWS",
        "Docker",
        "Kubernetes",
        "SQL",
        "Git",
        "Agile"
    ]
    return Response(popular_skills)

@api_view(['GET'])
def popular_industries(request):
    """获取热门行业列表"""
    # 模拟热门行业数据
    popular_industries = [
        "Technology",
        "Healthcare",
        "Finance",
        "Education",
        "E-commerce",
        "Manufacturing",
        "Consulting",
        "Media & Entertainment",
        "Real Estate",
        "Transportation"
    ]
    return Response(popular_industries) 