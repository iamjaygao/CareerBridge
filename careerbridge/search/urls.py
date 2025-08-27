from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('popular/jobs/', views.popular_jobs, name='popular_jobs'),
    path('popular/skills/', views.popular_skills, name='popular_skills'),
    path('popular/industries/', views.popular_industries, name='popular_industries'),
] 