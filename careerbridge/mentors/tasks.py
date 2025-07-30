from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .models import MentorProfile, MentorSession, MentorNotification, MentorPayment
from .services import MentorRecommendationService

@shared_task
def send_session_reminder_emails():
    """Send reminder emails for upcoming sessions"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    upcoming_sessions = MentorSession.objects.filter(
        scheduled_date=tomorrow,
        status__in=['confirmed', 'pending']
    ).select_related('mentor__user', 'user', 'service')
    
    for session in upcoming_sessions:
        # Send reminder to user
        send_session_reminder_to_user.delay(session.id)
        
        # Send reminder to mentor
        send_session_reminder_to_mentor.delay(session.id)

@shared_task
def send_session_reminder_to_user(session_id):
    """Send reminder email to user"""
    try:
        session = MentorSession.objects.get(id=session_id)
        
        context = {
            'session': session,
            'mentor': session.mentor,
            'user': session.user,
            'service': session.service
        }
        
        # Send email to user
        send_mail(
            subject=f"Reminder: Your session with {session.mentor.user.get_full_name()} tomorrow",
            message=render_to_string('mentors/emails/session_reminder_user.txt', context),
            from_email='noreply@careerbridge.com',
            recipient_list=[session.user.email],
            html_message=render_to_string('mentors/emails/session_reminder_user.html', context)
        )
        
        # Create notification
        MentorNotification.objects.create(
            mentor=session.mentor,
            notification_type='session_reminder',
            title='Session Reminder Sent',
            message=f'Reminder sent to {session.user.username} for tomorrow\'s session',
            related_session=session,
            is_sent=True
        )
        
    except MentorSession.DoesNotExist:
        pass

@shared_task
def send_session_reminder_to_mentor(session_id):
    """Send reminder email to mentor"""
    try:
        session = MentorSession.objects.get(id=session_id)
        
        context = {
            'session': session,
            'mentor': session.mentor,
            'user': session.user,
            'service': session.service
        }
        
        # Send email to mentor
        send_mail(
            subject=f"Reminder: Your session with {session.user.get_full_name()} tomorrow",
            message=render_to_string('mentors/emails/session_reminder_mentor.txt', context),
            from_email='noreply@careerbridge.com',
            recipient_list=[session.mentor.user.email],
            html_message=render_to_string('mentors/emails/session_reminder_mentor.html', context)
        )
        
    except MentorSession.DoesNotExist:
        pass

@shared_task
def process_pending_payments():
    """Process pending payments for completed sessions"""
    # Find completed sessions without payments
    completed_sessions = MentorSession.objects.filter(
        status='completed',
        mentor_payments__isnull=True
    ).select_related('mentor', 'service')
    
    for session in completed_sessions:
        process_session_payment.delay(session.id)

@shared_task
def process_session_payment(session_id):
    """Process payment for a specific session"""
    try:
        session = MentorSession.objects.get(id=session_id)
        
        # Calculate payment amounts
        if session.service.pricing_model == 'hourly':
            total_amount = session.service.price_per_hour * (session.duration_minutes / 60)
        elif session.service.pricing_model == 'fixed':
            total_amount = session.service.fixed_price
        else:  # package
            total_amount = session.service.package_price / session.service.package_sessions
        
        platform_fee = total_amount * (session.service.platform_fee_percentage / 100)
        mentor_earnings = total_amount * (session.service.mentor_earnings_percentage / 100)
        
        # Create payment record
        MentorPayment.objects.create(
            mentor=session.mentor,
            session=session,
            total_amount=total_amount,
            platform_fee=platform_fee,
            mentor_earnings=mentor_earnings,
            payment_method=session.mentor.preferred_payment_method,
            payment_status='pending'
        )
        
        # Send payment notification
        send_payment_notification.delay(session.mentor.id, session.id)
        
    except MentorSession.DoesNotExist:
        pass

@shared_task
def send_payment_notification(mentor_id, session_id):
    """Send payment notification to mentor"""
    try:
        mentor = MentorProfile.objects.get(id=mentor_id)
        session = MentorSession.objects.get(id=session_id)
        payment = MentorPayment.objects.get(session=session)
        
        context = {
            'mentor': mentor,
            'session': session,
            'payment': payment
        }
        
        # Send email notification
        send_mail(
            subject="Payment Received for Your Session",
            message=render_to_string('mentors/emails/payment_notification.txt', context),
            from_email='noreply@careerbridge.com',
            recipient_list=[mentor.user.email],
            html_message=render_to_string('mentors/emails/payment_notification.html', context)
        )
        
        # Create notification
        MentorNotification.objects.create(
            mentor=mentor,
            notification_type='payment_received',
            title='Payment Received',
            message=f'Payment of ${payment.mentor_earnings} received for session with {session.user.username}',
            related_session=session,
            related_payment=payment,
            is_sent=True
        )
        
    except (MentorProfile.DoesNotExist, MentorSession.DoesNotExist, MentorPayment.DoesNotExist):
        pass

@shared_task
def update_mentor_rankings():
    """Update mentor ranking scores and clear cache"""
    mentors = MentorProfile.objects.filter(status='approved')
    
    for mentor in mentors:
        # Force recalculation of ranking score
        ranking_score = mentor.ranking_score
        mentor.save()  # This will trigger ranking score recalculation
    
    # Clear recommendation cache
    MentorRecommendationService.clear_cache()

@shared_task
def send_weekly_mentor_report():
    """Send weekly report to mentors"""
    mentors = MentorProfile.objects.filter(status='approved')
    
    for mentor in mentors:
        send_mentor_weekly_report.delay(mentor.id)

@shared_task
def send_mentor_weekly_report(mentor_id):
    """Send weekly report to a specific mentor"""
    try:
        mentor = MentorProfile.objects.get(id=mentor_id)
        
        # Get analytics for the past week
        from .services import MentorAnalyticsService
        analytics = MentorAnalyticsService.get_mentor_analytics(mentor, days=7)
        
        context = {
            'mentor': mentor,
            'analytics': analytics
        }
        
        # Send email report
        send_mail(
            subject="Your Weekly Mentor Report",
            message=render_to_string('mentors/emails/weekly_report.txt', context),
            from_email='noreply@careerbridge.com',
            recipient_list=[mentor.user.email],
            html_message=render_to_string('mentors/emails/weekly_report.html', context)
        )
        
    except MentorProfile.DoesNotExist:
        pass

@shared_task
def cleanup_old_notifications():
    """Clean up old notifications (older than 90 days)"""
    cutoff_date = timezone.now() - timedelta(days=90)
    
    old_notifications = MentorNotification.objects.filter(
        created_at__lt=cutoff_date,
        is_read=True
    )
    
    deleted_count = old_notifications.count()
    old_notifications.delete()
    
    return f"Deleted {deleted_count} old notifications"

@shared_task
def send_application_status_update(application_id):
    """Send application status update email"""
    try:
        from .models import MentorApplication
        application = MentorApplication.objects.get(id=application_id)
        
        context = {
            'application': application,
            'user': application.user
        }
        
        if application.status == 'approved':
            subject = "Congratulations! Your Mentor Application Has Been Approved"
            template_txt = 'mentors/emails/application_approved.txt'
            template_html = 'mentors/emails/application_approved.html'
        else:
            subject = "Update on Your Mentor Application"
            template_txt = 'mentors/emails/application_rejected.txt'
            template_html = 'mentors/emails/application_rejected.html'
        
        send_mail(
            subject=subject,
            message=render_to_string(template_txt, context),
            from_email='noreply@careerbridge.com',
            recipient_list=[application.user.email],
            html_message=render_to_string(template_html, context)
        )
        
    except MentorApplication.DoesNotExist:
        pass

@shared_task
def process_refund_request(payment_id, refund_amount, reason):
    """Process refund request"""
    try:
        payment = MentorPayment.objects.get(id=payment_id)
        
        # Process refund through payment processor
        # This would integrate with Stripe/PayPal APIs
        payment.process_refund(refund_amount, reason)
        
        # Send refund notification
        send_refund_notification.delay(payment.id)
        
    except MentorPayment.DoesNotExist:
        pass

@shared_task
def send_refund_notification(payment_id):
    """Send refund notification"""
    try:
        payment = MentorPayment.objects.get(id=payment_id)
        
        context = {
            'payment': payment,
            'mentor': payment.mentor,
            'user': payment.session.user
        }
        
        # Send notification to user
        send_mail(
            subject="Refund Processed",
            message=render_to_string('mentors/emails/refund_notification.txt', context),
            from_email='noreply@careerbridge.com',
            recipient_list=[payment.session.user.email],
            html_message=render_to_string('mentors/emails/refund_notification.html', context)
        )
        
        # Send notification to mentor
        send_mail(
            subject="Refund Processed for Your Session",
            message=render_to_string('mentors/emails/refund_notification_mentor.txt', context),
            from_email='noreply@careerbridge.com',
            recipient_list=[payment.mentor.user.email],
            html_message=render_to_string('mentors/emails/refund_notification_mentor.html', context)
        )
        
    except MentorPayment.DoesNotExist:
        pass 