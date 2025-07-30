from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import (
    InvitationCode, ReferralProgram, UserReferralStats, 
    UserSubscription
)

class ReferralService:
    """Service for managing referral program"""
    
    def __init__(self):
        self.program = self._get_or_create_program()
    
    def _get_or_create_program(self):
        """Get or create referral program"""
        program, created = ReferralProgram.objects.get_or_create(
            is_active=True,
            defaults={
                'name': 'CareerBridge Referral Program',
                'max_invitations_per_user': 10,
                'invitation_expiry_days': 30,
                'inviter_reward_days': 7,
                'invitee_reward_days': 7,
                'milestone_5_invitations': 30,
                'milestone_10_invitations': 60,
                'milestone_20_invitations': 120
            }
        )
        return program
    
    def create_invitation(self, inviter, email):
        """Create invitation for a user"""
        
        if not self.program.is_active:
            raise ValueError("Referral program is not active")
        
        # Check if user has reached invitation limit
        stats = self._get_or_create_stats(inviter)
        if stats.invitations_sent >= self.program.max_invitations_per_user:
            raise ValueError(f"Maximum invitations ({self.program.max_invitations_per_user}) reached")
        
        # Check if email already has an invitation
        if InvitationCode.objects.filter(email=email, is_used=False, is_expired=False).exists():
            raise ValueError("Email already has a pending invitation")
        
        # Create invitation
        invitation = InvitationCode.objects.create(
            inviter=inviter,
            email=email,
            inviter_reward_days=self.program.inviter_reward_days,
            invitee_reward_days=self.program.invitee_reward_days,
            expires_at=timezone.now() + timezone.timedelta(days=self.program.invitation_expiry_days)
        )
        
        # Update stats
        stats.invitations_sent += 1
        stats.save()
        
        # Send invitation email
        self._send_invitation_email(invitation)
        
        return invitation
    
    def use_invitation(self, code, invitee_user):
        """Use invitation code"""
        
        try:
            invitation = InvitationCode.objects.get(code=code)
        except InvitationCode.DoesNotExist:
            raise ValueError("Invalid invitation code")
        
        if not invitation.is_valid():
            raise ValueError("Invitation code is expired or already used")
        
        if invitation.email != invitee_user.email:
            raise ValueError("Invitation code is not for this email")
        
        # Use invitation
        if invitation.use_invitation(invitee_user):
            # Update stats
            self._update_inviter_stats(invitation.inviter)
            self._check_milestones(invitation.inviter)
            return True
        
        return False
    
    def get_user_stats(self, user):
        """Get user referral statistics"""
        stats = self._get_or_create_stats(user)
        
        # Get pending invitations
        pending_invitations = InvitationCode.objects.filter(
            inviter=user,
            is_used=False,
            is_expired=False
        )
        
        # Get subscription info
        subscription = UserSubscription.objects.get_or_create(
            user=user,
            defaults={'tier': 'free'}
        )[0]
        
        return {
            'stats': {
                'invitations_sent': stats.invitations_sent,
                'invitations_used': stats.invitations_used,
                'invitations_expired': stats.invitations_expired,
                'conversion_rate': stats.conversion_rate,
                'total_rewards_earned': stats.total_rewards_earned,
                'total_rewards_used': stats.total_rewards_used,
                'available_rewards': stats.available_rewards,
                'milestone_5_reached': stats.milestone_5_reached,
                'milestone_10_reached': stats.milestone_10_reached,
                'milestone_20_reached': stats.milestone_20_reached,
            },
            'subscription': {
                'tier': subscription.tier,
                'free_days_earned': subscription.free_days_earned,
                'free_days_used': subscription.free_days_used,
                'available_free_days': subscription.available_free_days,
            },
            'pending_invitations': [
                {
                    'code': inv.code,
                    'email': inv.email,
                    'created_at': inv.created_at,
                    'expires_at': inv.expires_at,
                }
                for inv in pending_invitations
            ],
            'program_settings': {
                'max_invitations': self.program.max_invitations_per_user,
                'inviter_reward_days': self.program.inviter_reward_days,
                'invitee_reward_days': self.program.invitee_reward_days,
                'milestone_5_reward': self.program.milestone_5_invitations,
                'milestone_10_reward': self.program.milestone_10_invitations,
                'milestone_20_reward': self.program.milestone_20_invitations,
            }
        }
    
    def get_referral_link(self, user):
        """Generate referral link for user"""
        # This would be used for sharing on social media
        base_url = getattr(settings, 'FRONTEND_URL', 'https://careerbridge.com')
        return f"{base_url}/register?ref={user.username}"
    
    def _get_or_create_stats(self, user):
        """Get or create user referral stats"""
        stats, created = UserReferralStats.objects.get_or_create(user=user)
        return stats
    
    def _update_inviter_stats(self, inviter):
        """Update inviter statistics"""
        stats = self._get_or_create_stats(inviter)
        stats.invitations_used += 1
        stats.total_rewards_earned += self.program.inviter_reward_days
        stats.save()
    
    def _check_milestones(self, user):
        """Check and award milestone rewards"""
        stats = self._get_or_create_stats(user)
        subscription = UserSubscription.objects.get(user=user)
        
        # Check milestone 5
        if stats.invitations_used >= 5 and not stats.milestone_5_reached:
            stats.milestone_5_reached = True
            subscription.add_free_days(self.program.milestone_5_invitations)
            stats.total_rewards_earned += self.program.milestone_5_invitations
            self._send_milestone_email(user, 5, self.program.milestone_5_invitations)
        
        # Check milestone 10
        if stats.invitations_used >= 10 and not stats.milestone_10_reached:
            stats.milestone_10_reached = True
            subscription.add_free_days(self.program.milestone_10_invitations)
            stats.total_rewards_earned += self.program.milestone_10_invitations
            self._send_milestone_email(user, 10, self.program.milestone_10_invitations)
        
        # Check milestone 20
        if stats.invitations_used >= 20 and not stats.milestone_20_reached:
            stats.milestone_20_reached = True
            subscription.add_free_days(self.program.milestone_20_invitations)
            stats.total_rewards_earned += self.program.milestone_20_invitations
            self._send_milestone_email(user, 20, self.program.milestone_20_invitations)
        
        stats.save()
    
    def _send_invitation_email(self, invitation):
        """Send invitation email"""
        try:
            subject = f"Join CareerBridge - {invitation.inviter.username} invited you!"
            
            context = {
                'inviter_name': invitation.inviter.username,
                'invitation_code': invitation.code,
                'reward_days': invitation.invitee_reward_days,
                'expires_at': invitation.expires_at,
                'signup_url': f"{getattr(settings, 'FRONTEND_URL', 'https://careerbridge.com')}/register?code={invitation.code}"
            }
            
            html_message = render_to_string('emails/invitation.html', context)
            plain_message = render_to_string('emails/invitation.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Error sending invitation email: {e}")
    
    def _send_milestone_email(self, user, milestone, reward_days):
        """Send milestone achievement email"""
        try:
            subject = f"Congratulations! You've reached {milestone} referrals!"
            
            context = {
                'user_name': user.username,
                'milestone': milestone,
                'reward_days': reward_days,
                'total_rewards': UserReferralStats.objects.get(user=user).total_rewards_earned
            }
            
            html_message = render_to_string('emails/milestone.html', context)
            plain_message = render_to_string('emails/milestone.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Error sending milestone email: {e}")

class PricingService:
    """Service for managing pricing and subscriptions"""
    
    PRICING = {
        'free': {
            'monthly_price': 0.00,
            'yearly_price': 0.00,
            'features': [
                '3 resume uploads per month',
                '5 analyses per month',
                '10 JD matches per month',
                'Basic keyword matching',
                'Basic recommendations'
            ]
        },
        'premium': {
            'monthly_price': 9.99,
            'yearly_price': 99.00,  # Save 17%
            'features': [
                'Unlimited resume uploads',
                'Unlimited analyses',
                'Unlimited JD matches',
                'Advanced AI analysis',
                'Detailed recommendations',
                'User feedback system',
                'Priority support'
            ]
        },
        'enterprise': {
            'monthly_price': 49.99,
            'yearly_price': 499.00,  # Save 17%
            'features': [
                'All Premium features',
                'Batch processing',
                'API access',
                'External integrations',
                'Advanced analytics',
                'Dedicated support',
                'Custom solutions'
            ]
        }
    }
    
    @classmethod
    def get_pricing(cls, tier=None):
        """Get pricing information"""
        if tier:
            return cls.PRICING.get(tier, cls.PRICING['free'])
        return cls.PRICING
    
    @classmethod
    def calculate_savings(cls, tier, billing_cycle):
        """Calculate savings for yearly billing"""
        if billing_cycle == 'yearly':
            monthly_price = cls.PRICING[tier]['monthly_price']
            yearly_price = cls.PRICING[tier]['yearly_price']
            yearly_cost = monthly_price * 12
            savings = yearly_cost - yearly_price
            savings_percentage = (savings / yearly_cost) * 100
            return {
                'savings_amount': savings,
                'savings_percentage': savings_percentage
            }
        return {'savings_amount': 0, 'savings_percentage': 0}
    
    @classmethod
    def get_feature_comparison(cls):
        """Get feature comparison table"""
        return {
            'features': [
                'Resume Uploads',
                'AI Analysis',
                'JD Matching',
                'Recommendations',
                'User Feedback',
                'API Access',
                'Batch Processing',
                'Priority Support'
            ],
            'tiers': {
                'free': [3, 5, 10, 'Basic', 'No', 'No', 'No', 'No'],
                'premium': ['Unlimited', 'Unlimited', 'Unlimited', 'Advanced', 'Yes', 'No', 'No', 'Yes'],
                'enterprise': ['Unlimited', 'Unlimited', 'Unlimited', 'Advanced', 'Yes', 'Yes', 'Yes', 'Yes']
            }
        } 