from django.db.models import Q, Avg, Count, Sum
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from ..models import MentorProfile, MentorService, MentorReview, MentorSession

class MentorRecommendationService:
    """Service for mentor recommendations and rankings"""
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_top_mentors(cls, limit=10, category=None, industry=None):
        """Get top mentors by ranking score"""
        cache_key = f"top_mentors_{limit}_{category}_{industry}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        queryset = MentorProfile.objects.filter(
            status='approved',
            is_active=True
        )
        
        if category:
            queryset = queryset.filter(services__service_type=category)
        
        if industry:
            queryset = queryset.filter(industry=industry)
        
        # Calculate ranking score and order by it
        mentors = []
        for mentor in queryset.distinct():
            ranking_score = mentor.ranking_score
            mentors.append({
                'mentor': mentor,
                'ranking_score': ranking_score,
                'total_sessions': mentor.total_sessions,
                'average_rating': mentor.average_rating
            })
        
        # Sort by ranking score (70% rating + 30% sessions)
        mentors.sort(key=lambda x: x['ranking_score'], reverse=True)
        result = mentors[:limit]
        
        cache.set(cache_key, result, cls.CACHE_TIMEOUT)
        return result
    
    @classmethod
    def get_mentors_by_rating(cls, limit=10, min_rating=4.0):
        """Get mentors sorted by average rating"""
        cache_key = f"mentors_by_rating_{limit}_{min_rating}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        mentors = MentorProfile.objects.filter(
            status='approved',
            average_rating__gte=min_rating,
            total_reviews__gte=3  # Minimum reviews for credibility
        ).order_by('-average_rating', '-total_reviews')[:limit]
        
        cache.set(cache_key, list(mentors), cls.CACHE_TIMEOUT)
        return mentors
    
    @classmethod
    def get_mentors_by_sessions(cls, limit=10, days=30):
        """Get mentors sorted by number of sessions in recent period"""
        cache_key = f"mentors_by_sessions_{limit}_{days}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        start_date = timezone.now() - timedelta(days=days)
        
        mentors = MentorProfile.objects.filter(
            status='approved',
            sessions__status='completed',
            sessions__completed_at__gte=start_date
        ).annotate(
            recent_sessions=Count('sessions')
        ).order_by('-recent_sessions', '-average_rating')[:limit]
        
        cache.set(cache_key, list(mentors), cls.CACHE_TIMEOUT)
        return mentors
    
    @classmethod
    def get_mentors_by_earnings(cls, limit=10, days=30):
        """Get mentors sorted by earnings in recent period"""
        cache_key = f"mentors_by_earnings_{limit}_{days}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        start_date = timezone.now() - timedelta(days=days)
        
        mentors = MentorProfile.objects.filter(
            status='approved',
            payments__payment_status='completed',
            payments__processed_at__gte=start_date
        ).annotate(
            recent_earnings=Sum('payments__mentor_earnings')
        ).order_by('-recent_earnings', '-average_rating')[:limit]
        
        cache.set(cache_key, list(mentors), cls.CACHE_TIMEOUT)
        return mentors
    
    @classmethod
    def get_recommended_mentors(cls, user, service_type=None, limit=10):
        """Get personalized mentor recommendations for a user"""
        cache_key = f"recommended_mentors_{user.id}_{service_type}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Base query for approved mentors
        queryset = MentorProfile.objects.filter(status='approved')
        
        # Filter by service type if specified
        if service_type:
            queryset = queryset.filter(services__service_type=service_type)
        
        # Get user's previous interactions
        user_reviews = MentorReview.objects.filter(user=user)
        user_sessions = MentorSession.objects.filter(user=user)
        
        # Calculate recommendation scores
        mentors = []
        for mentor in queryset.distinct():
            score = cls._calculate_recommendation_score(mentor, user, user_reviews, user_sessions)
            if score > 0:
                mentors.append({
                    'mentor': mentor,
                    'recommendation_score': score,
                    'reasons': cls._get_recommendation_reasons(mentor, user)
                })
        
        # Sort by recommendation score
        mentors.sort(key=lambda x: x['recommendation_score'], reverse=True)
        result = mentors[:limit]
        
        cache.set(cache_key, result, cls.CACHE_TIMEOUT)
        return result
    
    @classmethod
    def _calculate_recommendation_score(cls, mentor, user, user_reviews, user_sessions):
        """Calculate personalized recommendation score"""
        score = 0.0
        
        # Base score from mentor's overall performance
        score += mentor.average_rating * 0.3
        score += min(mentor.total_sessions / 50, 2.0) * 0.2  # Experience bonus
        
        # Verification bonus
        if mentor.is_verified:
            score += 0.5
        
        # Industry match (if user has preferences)
        # This could be enhanced with user profile data
        
        # Avoid mentors the user has already worked with
        if user_sessions.filter(mentor=mentor).exists():
            score -= 1.0
        
        # Recent activity bonus
        recent_sessions = mentor.sessions.filter(
            status='completed',
            completed_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        score += min(recent_sessions / 10, 1.0) * 0.1
        
        return max(score, 0.0)
    
    @classmethod
    def _get_recommendation_reasons(cls, mentor, user):
        """Get reasons why this mentor is recommended"""
        reasons = []
        
        if mentor.average_rating >= 4.5:
            reasons.append("High rating")
        
        if mentor.total_sessions >= 20:
            reasons.append("Experienced")
        
        if mentor.is_verified:
            reasons.append("Verified mentor")
        
        if mentor.total_reviews >= 10:
            reasons.append("Well-reviewed")
        
        return reasons

class MentorSearchService:
    """Service for advanced mentor search"""
    
    @classmethod
    def search_mentors(cls, query=None, service_type=None, industry=None, 
                      min_rating=None, max_price=None, is_verified=None,
                      availability_day=None, availability_time=None):
        """Advanced mentor search with multiple filters"""
        
        queryset = MentorProfile.objects.filter(status='approved')
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(user__username__icontains=query) |
                Q(current_position__icontains=query) |
                Q(bio__icontains=query) |
                Q(industry__icontains=query)
            )
        
        # Service type filter
        if service_type:
            queryset = queryset.filter(services__service_type=service_type)
        
        # Industry filter
        if industry:
            queryset = queryset.filter(industry=industry)
        
        # Rating filter
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        # Price filter
        if max_price:
            queryset = queryset.filter(
                services__price_per_hour__lte=max_price
            )
        
        # Verification filter
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified)
        
        # Availability filter
        if availability_day is not None:
            queryset = queryset.filter(
                availabilities__day_of_week=availability_day,
                availabilities__is_active=True
            )
        
        return queryset.distinct().order_by('-ranking_score')

class MentorAnalyticsService:
    """Service for mentor analytics and insights"""
    
    @classmethod
    def get_mentor_analytics(cls, mentor, days=30):
        """Get comprehensive analytics for a mentor"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Session analytics
        sessions = MentorSession.objects.filter(
            mentor=mentor,
            created_at__gte=start_date
        )
        
        session_stats = {
            'total_sessions': sessions.count(),
            'completed_sessions': sessions.filter(status='completed').count(),
            'cancelled_sessions': sessions.filter(status='cancelled').count(),
            'completion_rate': 0
        }
        
        if session_stats['total_sessions'] > 0:
            session_stats['completion_rate'] = (
                session_stats['completed_sessions'] / session_stats['total_sessions']
            ) * 100
        
        # Revenue analytics
        payments = MentorPayment.objects.filter(
            mentor=mentor,
            created_at__gte=start_date
        )
        
        revenue_stats = {
            'total_revenue': payments.filter(payment_status='completed').aggregate(
                total=Sum('mentor_earnings')
            )['total'] or 0,
            'pending_revenue': payments.filter(payment_status='pending').aggregate(
                total=Sum('mentor_earnings')
            )['total'] or 0,
            'refunded_amount': payments.filter(payment_status='refunded').aggregate(
                total=Sum('refund_amount')
            )['total'] or 0
        }
        
        # Review analytics
        reviews = MentorReview.objects.filter(
            mentor=mentor,
            created_at__gte=start_date
        )
        
        review_stats = {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
            'rating_distribution': {}
        }
        
        # Rating distribution
        for rating in range(1, 6):
            count = reviews.filter(rating=rating).count()
            review_stats['rating_distribution'][rating] = count
        
        return {
            'session_stats': session_stats,
            'revenue_stats': revenue_stats,
            'review_stats': review_stats,
            'period_days': days
        }
    
    @classmethod
    def get_platform_analytics(cls, days=30):
        """Get platform-wide analytics"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Overall statistics
        total_mentors = MentorProfile.objects.filter(status='approved').count()
        active_mentors = MentorProfile.objects.filter(
            status='approved',
            sessions__created_at__gte=start_date
        ).distinct().count()
        
        # Session statistics
        total_sessions = MentorSession.objects.filter(created_at__gte=start_date).count()
        completed_sessions = MentorSession.objects.filter(
            status='completed',
            created_at__gte=start_date
        ).count()
        
        # Revenue statistics
        total_revenue = MentorPayment.objects.filter(
            payment_status='completed',
            created_at__gte=start_date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        platform_fees = MentorPayment.objects.filter(
            payment_status='completed',
            created_at__gte=start_date
        ).aggregate(total=Sum('platform_fee'))['total'] or 0
        
        return {
            'total_mentors': total_mentors,
            'active_mentors': active_mentors,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'completion_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'total_revenue': total_revenue,
            'platform_fees': platform_fees,
            'period_days': days
        } 
    # mentors/services.py

def apply_track_ranking(queryset, track: str):
    """
    Apply different ranking strategies based on primary_track
    """
    if track == "resume_review":
        return queryset.order_by(
            "-average_rating",
            "-total_sessions",
            "-is_verified",
        )

    if track == "mock_interview":
        return queryset.order_by(
            "-total_sessions",
            "-average_rating",
        )

    if track == "career_switch":
        return queryset.order_by(
            "-is_verified",
            "-total_sessions",
        )

    if track == "advanced_interview":
        return queryset.order_by(
            "-average_rating",
            "-is_verified",
            "-total_sessions",
        )

    return queryset.order_by(
        "-is_verified",
        "-average_rating",
        "-total_sessions",
    )
