from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Resume, ResumeAnalysis, ResumeFeedback,
    ResumeComparison, ResumeTemplate, ResumeExport,
    JobDescription, ResumeJobMatch
)

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'file_size_display', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'file_size_display')
    
    def file_size_display(self, obj):
        """Display file size in human readable format"""
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb < 1024:
                return f"{size_kb:.1f} KB"
            else:
                size_mb = size_kb / 1024
                return f"{size_mb:.1f} MB"
        return "N/A"
    file_size_display.short_description = "File Size"

@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('resume_title', 'user', 'overall_score', 'score_category', 'processing_time', 'created_at')
    list_filter = ('analysis_version', 'created_at')
    search_fields = ('resume__title', 'resume__user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def resume_title(self, obj):
        return obj.resume.title if obj.resume else "N/A"
    resume_title.short_description = "Resume"
    
    def user(self, obj):
        return obj.resume.user.username if obj.resume and obj.resume.user else "N/A"
    user.short_description = "User"
    
    def score_category(self, obj):
        """Get score category with color coding"""
        if obj.overall_score >= 90:
            color = "green"
            category = "Excellent"
        elif obj.overall_score >= 80:
            color = "blue"
            category = "Good"
        elif obj.overall_score >= 70:
            color = "orange"
            category = "Fair"
        elif obj.overall_score >= 60:
            color = "red"
            category = "Poor"
        else:
            color = "gray"
            category = "Very Poor"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, category
        )
    score_category.short_description = "Score Category"

@admin.register(ResumeFeedback)
class ResumeFeedbackAdmin(admin.ModelAdmin):
    list_display = ('analysis', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('analysis__resume__title', 'summary')

@admin.register(ResumeComparison)
class ResumeComparisonAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'comparison_type', 'overall_improvement', 'created_at')
    list_filter = ('comparison_type', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'industry', 'is_active', 'created_at')
    list_filter = ('template_type', 'industry', 'is_active', 'created_at')
    search_fields = ('name', 'description')

@admin.register(ResumeExport)
class ResumeExportAdmin(admin.ModelAdmin):
    list_display = ('resume_title', 'export_format', 'file_size', 'created_at')
    list_filter = ('export_format', 'created_at')
    search_fields = ('resume__title',)
    readonly_fields = ('created_at', 'downloaded_at')
    
    def resume_title(self, obj):
        return obj.resume.title if obj.resume else "N/A"
    resume_title.short_description = "Resume"

@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'job_type', 'source', 'total_skills_display', 'created_at')
    list_filter = ('job_type', 'source', 'is_processed', 'created_at')
    search_fields = ('title', 'company', 'location', 'description')
    readonly_fields = ('created_at', 'updated_at', 'total_skills_display', 'skill_density_display')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'location', 'description')
        }),
        ('Requirements', {
            'fields': ('required_skills', 'preferred_skills', 'experience_level', 'education_level', 'salary_range', 'job_type')
        }),
        ('Metadata', {
            'fields': ('source', 'source_url', 'is_processed', 'processing_errors')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'crawled_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_skills_display', 'skill_density_display'),
            'classes': ('collapse',)
        })
    )
    
    def total_skills_display(self, obj):
        """Display total number of skills"""
        return obj.total_skills
    total_skills_display.short_description = "Total Skills"
    
    def skill_density_display(self, obj):
        """Display skill density"""
        return f"{obj.skill_density:.4f}"
    skill_density_display.short_description = "Skill Density"

@admin.register(ResumeJobMatch)
class ResumeJobMatchAdmin(admin.ModelAdmin):
    list_display = ('resume_title', 'job_title', 'company_name', 'overall_match_score', 'match_level_display', 'created_at')
    list_filter = ('match_level', 'created_at')
    search_fields = ('resume__title', 'job_description__title', 'job_description__company')
    readonly_fields = ('created_at', 'updated_at', 'match_level_display')
    
    fieldsets = (
        ('Match Information', {
            'fields': ('resume', 'job_description')
        }),
        ('Scores', {
            'fields': ('overall_match_score', 'skill_match_score', 'experience_match_score', 'education_match_score')
        }),
        ('Match Details', {
            'fields': ('matched_skills', 'missing_skills', 'skill_gaps', 'match_level', 'match_recommendations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def resume_title(self, obj):
        return obj.resume.title if obj.resume else "N/A"
    resume_title.short_description = "Resume"
    
    def job_title(self, obj):
        return obj.job_description.title if obj.job_description else "N/A"
    job_title.short_description = "Job"
    
    def company_name(self, obj):
        return obj.job_description.company if obj.job_description else "N/A"
    company_name.short_description = "Company"
    
    def match_level_display(self, obj):
        """Display match level with color coding"""
        colors = {
            'excellent': 'green',
            'good': 'blue',
            'fair': 'orange',
            'poor': 'red',
            'no_match': 'gray'
        }
        
        color = colors.get(obj.match_level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.match_level.title()
        )
    match_level_display.short_description = "Match Level"
