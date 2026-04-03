from django.urls import path
from . import views

app_name = 'ats_signals'  # Backward compatibility: old name 'resumes' still works via URL redirect

urlpatterns = [
    # Resume management
    path('', views.ResumeListView.as_view(), name='resume-list'),
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='resume-detail'),
    path('<int:pk>/download/', views.ResumeDownloadView.as_view(), name='resume-download'),

    # Resume analysis
    path('analyze/', views.ResumeAnalysisView.as_view(), name='resume-analyze'),
    path('jd-match/', views.JDMatchView.as_view(), name='jd-match'),
    path('analysis/<int:pk>/', views.ResumeAnalysisDetailView.as_view(), name='analysis-detail'),
    path('<int:resume_id>/analysis/', views.ResumeAnalysisByResumeView.as_view(), name='analysis-by-resume'),
    path('feedback/<int:pk>/', views.ResumeFeedbackView.as_view(), name='feedback-detail'),
    path('<int:resume_id>/feedback/', views.ResumeFeedbackByResumeView.as_view(), name='feedback-by-resume'),

    # Search and filtering
    path('search/', views.ResumeSearchView.as_view(), name='resume-search'),
    path('filter/', views.ResumeFilterView.as_view(), name='resume-filter'),

    # Statistics
    path('stats/', views.ResumeStatsView.as_view(), name='resume-stats'),

    # Enhanced Resume comparison
    path('comparisons/', views.ResumeComparisonView.as_view(), name='comparison-list'),

    # Templates
    path('templates/', views.ResumeTemplateListView.as_view(), name='template-list'),

    # Export
    path('exports/', views.ResumeExportView.as_view(), name='export-list'),
    path('exports/<int:pk>/', views.ResumeExportDetailView.as_view(), name='export-detail'),

    # Job Description management
    path('jobs/', views.JobDescriptionListView.as_view(), name='job-list'),
    path('jobs/<int:pk>/', views.JobDescriptionDetailView.as_view(), name='job-detail'),
    
    # External service integration
    path('jobs/crawl/', views.ExternalJobCrawlerView.as_view(), name='external-job-crawl'),
    path('jobs/search/', views.JobCrawlerSearchView.as_view(), name='job-crawler-search'),
    path('jobs/trending/', views.JobCrawlerTrendingView.as_view(), name='job-crawler-trending'),
    
    # Resume-Job matching with external service
    path('matches/', views.ResumeJobMatchView.as_view(), name='match-list'),
    path('matches/<int:pk>/', views.ResumeJobMatchDetailView.as_view(), name='match-detail'),
    path('matches/external/', views.ExternalResumeMatcherView.as_view(), name='external-match'),

    # External services health
    path('services/health/', views.ExternalServicesHealthView.as_view(), name='external-services-health'),
    path('external-services/health/', views.ExternalServicesHealthView.as_view(), name='external-services-health-alt'),
    
    # Job recommendations
    path('recommendations/', views.JobRecommendationView.as_view(), name='job-recommendations'),
    
    # Market data endpoints
    path('market/salary/', views.JobCrawlerSalaryView.as_view(), name='job-crawler-salary'),
    path('market/skills/', views.JobCrawlerSkillsView.as_view(), name='job-crawler-skills'),
    
    # Auto matching
    path('auto-match/', views.AutoMatchView.as_view(), name='auto-match'),

    # Tier-based functionality
    path('subscription/', views.UserSubscriptionView.as_view(), name='subscription'),
    path('keyword-match/', views.KeywordMatchView.as_view(), name='keyword-match'),
    path('premium-analysis/', views.PremiumAnalysisView.as_view(), name='premium-analysis'),
    path('matches/<int:pk>/feedback/', views.FeedbackView.as_view(), name='match-feedback'),
    
    # Enterprise functionality
    # path('api-configs/', views.ExternalAPIConfigView.as_view(), name='api-configs'),  # Removed - moved to external services
    path('batch-analysis/', views.BatchAnalysisView.as_view(), name='batch-analysis'),

    # Referral and pricing functionality
    path('referral/stats/', views.ReferralStatsView.as_view(), name='referral-stats'),
    path('referral/invite/', views.CreateInvitationView.as_view(), name='create-invitation'),
    path('referral/use/', views.UseInvitationView.as_view(), name='use-invitation'),
    path('referral/link/', views.ReferralLinkView.as_view(), name='referral-link'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('pricing/<str:tier>/', views.PricingDetailView.as_view(), name='pricing-detail'),
    path('subscription/upgrade/', views.SubscriptionUpgradeView.as_view(), name='subscription-upgrade'),
    path('free-days/use/', views.FreeDaysUsageView.as_view(), name='free-days-usage'),

    # Legal compliance and data management
    path('legal/disclaimers/', views.LegalDisclaimerListView.as_view(), name='disclaimer-list'),
    path('legal/disclaimers/<str:disclaimer_type>/', views.LegalDisclaimerDetailView.as_view(), name='disclaimer-detail'),
    path('legal/consent/', views.DataConsentView.as_view(), name='data-consent'),
    path('legal/consent/revoke/', views.RevokeConsentView.as_view(), name='revoke-consent'),
    
    # Data deletion
    path('data/deletion/request/', views.DataDeletionRequestView.as_view(), name='data-deletion-request'),
    path('data/deletion/requests/', views.DataDeletionRequestListView.as_view(), name='data-deletion-requests'),
    path('data/deletion/verify/<int:request_id>/<str:token>/', views.DataDeletionVerificationView.as_view(), name='data-deletion-verify'),
    path('data/deletion/status/', views.DataDeletionStatusView.as_view(), name='data-deletion-status'),
    
    # Privacy and data rights
    path('privacy/rights/', views.PrivacyRightsView.as_view(), name='privacy-rights'),
    path('privacy/export/', views.DataExportView.as_view(), name='data-export'),
    path('privacy/export/status/', views.DataExportStatusView.as_view(), name='data-export-status'),
    # path('privacy/retention/', views.DataRetentionView.as_view(), name='data-retention'),
    
    # External service management - TODO: Implement these views
    # path('services/', views.ExternalServiceListView.as_view(), name='external-service-list'),
    # path('services/<int:pk>/', views.ExternalServiceDetailView.as_view(), name='external-service-detail'),
    # path('services/<int:pk>/test/', views.TestExternalServiceView.as_view(), name='test-external-service'),
    # path('services/logs/', views.ServiceUsageLogView.as_view(), name='service-usage-logs'),
    
    # ATS Signals Dashboard
    path('ats-signals/', views.ATSSignalListView.as_view(), name='ats-signal-list'),
    path('ats-signals/<int:pk>/', views.ATSSignalDetailView.as_view(), name='ats-signal-detail'),
]
