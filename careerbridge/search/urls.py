from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_all, name='search_all'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
    path('trending/', views.trending_searches, name='trending_searches'),
    path('filters/', views.search_filters, name='search_filters'),
    path('history/', views.search_history, name='search_history'),
    path('analytics/', views.search_analytics, name='search_analytics'),
    path('popular/jobs/', views.popular_jobs, name='popular_jobs'),
    path('popular/skills/', views.popular_skills, name='popular_skills'),
    path('popular/industries/', views.popular_industries, name='popular_industries'),
]
