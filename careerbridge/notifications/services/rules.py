"""Notification rules and semantics."""

from enum import Enum
from typing import Dict, List, Optional


class Role(str, Enum):
    STUDENT = "student"
    MENTOR = "mentor"
    STAFF = "staff"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class NotificationCategory(str, Enum):
    ACTION_REQUIRED = "action_required"
    INFORMATIONAL = "informational"
    SYSTEM = "system"


class NotificationType(str, Enum):
    APPOINTMENT_PAYMENT_SUCCESS = "APPOINTMENT_PAYMENT_SUCCESS"
    APPOINTMENT_PAYMENT_FAILED = "APPOINTMENT_PAYMENT_FAILED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_CONFIRMED = "APPOINTMENT_CONFIRMED"
    APPOINTMENT_REJECTED = "APPOINTMENT_REJECTED"
    APPOINTMENT_EXPIRED = "APPOINTMENT_EXPIRED"
    APPOINTMENT_REVIEW_REMINDER = "APPOINTMENT_REVIEW_REMINDER"
    APPOINTMENT_RESCHEDULED = "APPOINTMENT_RESCHEDULED"
    MENTOR_SUBMITTED_FEEDBACK = "MENTOR_SUBMITTED_FEEDBACK"
    UPCOMING_APPOINTMENT_REMINDER = "UPCOMING_APPOINTMENT_REMINDER"
    MENTOR_APPLICATION_SUBMITTED = "MENTOR_APPLICATION_SUBMITTED"
    MENTOR_APPLICATION_APPROVED = "MENTOR_APPLICATION_APPROVED"
    MENTOR_APPLICATION_REJECTED = "MENTOR_APPLICATION_REJECTED"
    RESUME_UPLOADED = "RESUME_UPLOADED"
    SYSTEM_ANNOUNCEMENT = "SYSTEM_ANNOUNCEMENT"
    SUPPORT_TICKET_CREATED = "SUPPORT_TICKET_CREATED"
    STAFF_APPOINTMENT_CANCELLED = "STAFF_APPOINTMENT_CANCELLED"
    STAFF_PAYMENT_FAILED = "STAFF_PAYMENT_FAILED"
    STAFF_USER_FEEDBACK_SUBMITTED = "STAFF_USER_FEEDBACK_SUBMITTED"
    STAFF_USER_REPORTED = "STAFF_USER_REPORTED"
    STAFF_CHAT_NO_RESPONSE = "STAFF_CHAT_NO_RESPONSE"
    STAFF_APPOINTMENT_UPCOMING = "STAFF_APPOINTMENT_UPCOMING"
    STAFF_MENTOR_NO_CONFIRM = "STAFF_MENTOR_NO_CONFIRM"
    STAFF_MENTOR_NO_FEEDBACK = "STAFF_MENTOR_NO_FEEDBACK"
    STAFF_REPEAT_FAILURE = "STAFF_REPEAT_FAILURE"
    ADMIN_MENTOR_PROFILE_UPDATED = "ADMIN_MENTOR_PROFILE_UPDATED"
    ADMIN_RISK_ALERT = "ADMIN_RISK_ALERT"
    ADMIN_SLOT_CONFLICT = "ADMIN_SLOT_CONFLICT"
    ADMIN_REFUND_ALERT = "ADMIN_REFUND_ALERT"
    ADMIN_MENTOR_LOW_RATING = "ADMIN_MENTOR_LOW_RATING"
    ADMIN_METRIC_ANOMALY = "ADMIN_METRIC_ANOMALY"
    ADMIN_PAYMENT_SUCCESS_DROP = "ADMIN_PAYMENT_SUCCESS_DROP"
    SUPERADMIN_SYSTEM_ALERT = "SUPERADMIN_SYSTEM_ALERT"
    SUPERADMIN_SECURITY_ALERT = "SUPERADMIN_SECURITY_ALERT"
    SUPERADMIN_RULE_CHANGE = "SUPERADMIN_RULE_CHANGE"


class NotificationRule:
    def __init__(
        self,
        *,
        type: NotificationType,
        category: NotificationCategory,
        recipients: List[Role],
        dedupe_key: Optional[str] = None,
        description: str = "",
    ):
        self.type = type
        self.category = category
        self.recipients = recipients
        self.dedupe_key = dedupe_key
        self.description = description


NOTIFICATION_TYPE_MAP: Dict[NotificationType, str] = {
    NotificationType.APPOINTMENT_PAYMENT_SUCCESS: "payment_success",
    NotificationType.APPOINTMENT_PAYMENT_FAILED: "payment_failed",
    NotificationType.APPOINTMENT_CANCELLED: "appointment_cancelled",
    NotificationType.APPOINTMENT_CONFIRMED: "appointment_confirmed",
    NotificationType.APPOINTMENT_REJECTED: "appointment_rejected",
    NotificationType.APPOINTMENT_EXPIRED: "appointment_expired",
    NotificationType.APPOINTMENT_REVIEW_REMINDER: "system_announcement",
    NotificationType.APPOINTMENT_RESCHEDULED: "appointment_rescheduled",
    NotificationType.MENTOR_SUBMITTED_FEEDBACK: "feedback_submitted",
    NotificationType.UPCOMING_APPOINTMENT_REMINDER: "appointment_reminder",
    NotificationType.MENTOR_APPLICATION_SUBMITTED: "mentor_application_submitted",
    NotificationType.MENTOR_APPLICATION_APPROVED: "mentor_application_approved",
    NotificationType.MENTOR_APPLICATION_REJECTED: "mentor_application_rejected",
    NotificationType.RESUME_UPLOADED: "resume_uploaded",
    NotificationType.SYSTEM_ANNOUNCEMENT: "system_announcement",
    NotificationType.SUPPORT_TICKET_CREATED: "support_ticket_created",
    NotificationType.STAFF_APPOINTMENT_CANCELLED: "staff_appointment_cancelled",
    NotificationType.STAFF_PAYMENT_FAILED: "staff_payment_failed",
    NotificationType.STAFF_USER_FEEDBACK_SUBMITTED: "staff_user_feedback_submitted",
    NotificationType.STAFF_USER_REPORTED: "staff_user_reported",
    NotificationType.STAFF_CHAT_NO_RESPONSE: "staff_chat_no_response",
    NotificationType.STAFF_APPOINTMENT_UPCOMING: "staff_appointment_upcoming",
    NotificationType.STAFF_MENTOR_NO_CONFIRM: "staff_mentor_no_confirm",
    NotificationType.STAFF_MENTOR_NO_FEEDBACK: "staff_mentor_no_feedback",
    NotificationType.STAFF_REPEAT_FAILURE: "staff_repeat_failure",
    NotificationType.ADMIN_MENTOR_PROFILE_UPDATED: "admin_mentor_profile_updated",
    NotificationType.ADMIN_RISK_ALERT: "admin_risk_alert",
    NotificationType.ADMIN_SLOT_CONFLICT: "admin_slot_conflict",
    NotificationType.ADMIN_REFUND_ALERT: "admin_refund_alert",
    NotificationType.ADMIN_MENTOR_LOW_RATING: "admin_mentor_low_rating",
    NotificationType.ADMIN_METRIC_ANOMALY: "admin_metric_anomaly",
    NotificationType.ADMIN_PAYMENT_SUCCESS_DROP: "admin_payment_success_drop",
    NotificationType.SUPERADMIN_SYSTEM_ALERT: "superadmin_system_alert",
    NotificationType.SUPERADMIN_SECURITY_ALERT: "superadmin_security_alert",
    NotificationType.SUPERADMIN_RULE_CHANGE: "superadmin_rule_change",
}


NOTIFICATION_RULES: Dict[NotificationType, NotificationRule] = {
    NotificationType.APPOINTMENT_PAYMENT_SUCCESS: NotificationRule(
        type=NotificationType.APPOINTMENT_PAYMENT_SUCCESS,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STUDENT],
        dedupe_key="appointment_id",
        description="Payment completed successfully for an appointment.",
    ),
    NotificationType.APPOINTMENT_PAYMENT_FAILED: NotificationRule(
        type=NotificationType.APPOINTMENT_PAYMENT_FAILED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STUDENT],
        dedupe_key="appointment_id",
        description="Payment failed or expired; user action required.",
    ),
    NotificationType.APPOINTMENT_CANCELLED: NotificationRule(
        type=NotificationType.APPOINTMENT_CANCELLED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STUDENT, Role.MENTOR],
        dedupe_key="appointment_id",
        description="An appointment has been cancelled.",
    ),
    NotificationType.APPOINTMENT_CONFIRMED: NotificationRule(
        type=NotificationType.APPOINTMENT_CONFIRMED,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STUDENT, Role.MENTOR],
        dedupe_key="appointment_id",
        description="An appointment has been confirmed.",
    ),
    NotificationType.APPOINTMENT_REJECTED: NotificationRule(
        type=NotificationType.APPOINTMENT_REJECTED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STUDENT],
        dedupe_key="appointment_id",
        description="An appointment request was rejected.",
    ),
    NotificationType.APPOINTMENT_EXPIRED: NotificationRule(
        type=NotificationType.APPOINTMENT_EXPIRED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STUDENT],
        dedupe_key="appointment_id",
        description="An appointment lock expired.",
    ),
    NotificationType.APPOINTMENT_REVIEW_REMINDER: NotificationRule(
        type=NotificationType.APPOINTMENT_REVIEW_REMINDER,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STUDENT],
        dedupe_key="appointment_id",
        description="Prompt student to review a completed session.",
    ),
    NotificationType.APPOINTMENT_RESCHEDULED: NotificationRule(
        type=NotificationType.APPOINTMENT_RESCHEDULED,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STUDENT, Role.MENTOR],
        dedupe_key="appointment_id",
        description="An appointment has been rescheduled.",
    ),
    NotificationType.MENTOR_SUBMITTED_FEEDBACK: NotificationRule(
        type=NotificationType.MENTOR_SUBMITTED_FEEDBACK,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STUDENT],
        dedupe_key="appointment_id",
        description="Mentor received a new review.",
    ),
    NotificationType.UPCOMING_APPOINTMENT_REMINDER: NotificationRule(
        type=NotificationType.UPCOMING_APPOINTMENT_REMINDER,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STUDENT, Role.MENTOR],
        dedupe_key="appointment_id",
        description="Upcoming appointment reminder.",
    ),
    NotificationType.MENTOR_APPLICATION_SUBMITTED: NotificationRule(
        type=NotificationType.MENTOR_APPLICATION_SUBMITTED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.ADMIN],
        dedupe_key="mentor_application_id",
        description="A mentor application was submitted.",
    ),
    NotificationType.MENTOR_APPLICATION_APPROVED: NotificationRule(
        type=NotificationType.MENTOR_APPLICATION_APPROVED,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.MENTOR],
        dedupe_key="mentor_application_id",
        description="Mentor application approved.",
    ),
    NotificationType.MENTOR_APPLICATION_REJECTED: NotificationRule(
        type=NotificationType.MENTOR_APPLICATION_REJECTED,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.MENTOR],
        dedupe_key="mentor_application_id",
        description="Mentor application rejected.",
    ),
    NotificationType.RESUME_UPLOADED: NotificationRule(
        type=NotificationType.RESUME_UPLOADED,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STUDENT],
        dedupe_key="resume_id",
        description="Resume uploaded successfully.",
    ),
    NotificationType.SYSTEM_ANNOUNCEMENT: NotificationRule(
        type=NotificationType.SYSTEM_ANNOUNCEMENT,
        category=NotificationCategory.SYSTEM,
        recipients=[
            Role.STUDENT,
            Role.MENTOR,
            Role.STAFF,
            Role.ADMIN,
            Role.SUPERADMIN,
        ],
        dedupe_key=None,
        description="System-wide announcement.",
    ),
    NotificationType.SUPPORT_TICKET_CREATED: NotificationRule(
        type=NotificationType.SUPPORT_TICKET_CREATED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="support_ticket_id",
        description="A support ticket requires staff action.",
    ),
    NotificationType.STAFF_APPOINTMENT_CANCELLED: NotificationRule(
        type=NotificationType.STAFF_APPOINTMENT_CANCELLED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="appointment_id",
        description="An appointment was cancelled and may need follow-up.",
    ),
    NotificationType.STAFF_PAYMENT_FAILED: NotificationRule(
        type=NotificationType.STAFF_PAYMENT_FAILED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="payment_id",
        description="Payment failed and may need staff follow-up.",
    ),
    NotificationType.STAFF_USER_FEEDBACK_SUBMITTED: NotificationRule(
        type=NotificationType.STAFF_USER_FEEDBACK_SUBMITTED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="feedback_id",
        description="User feedback requires staff review.",
    ),
    NotificationType.STAFF_USER_REPORTED: NotificationRule(
        type=NotificationType.STAFF_USER_REPORTED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="report_id",
        description="A user report requires staff review.",
    ),
    NotificationType.STAFF_CHAT_NO_RESPONSE: NotificationRule(
        type=NotificationType.STAFF_CHAT_NO_RESPONSE,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="conversation_id",
        description="Mentor has not replied in time.",
    ),
    NotificationType.STAFF_APPOINTMENT_UPCOMING: NotificationRule(
        type=NotificationType.STAFF_APPOINTMENT_UPCOMING,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.STAFF],
        dedupe_key="appointment_id",
        description="Upcoming appointment reminder for staff follow-up.",
    ),
    NotificationType.STAFF_MENTOR_NO_CONFIRM: NotificationRule(
        type=NotificationType.STAFF_MENTOR_NO_CONFIRM,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="appointment_id",
        description="Mentor did not confirm appointment in time.",
    ),
    NotificationType.STAFF_MENTOR_NO_FEEDBACK: NotificationRule(
        type=NotificationType.STAFF_MENTOR_NO_FEEDBACK,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="appointment_id",
        description="Mentor did not submit feedback after session.",
    ),
    NotificationType.STAFF_REPEAT_FAILURE: NotificationRule(
        type=NotificationType.STAFF_REPEAT_FAILURE,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.STAFF],
        dedupe_key="user_id",
        description="User experienced repeated failures that need follow-up.",
    ),
    NotificationType.ADMIN_MENTOR_PROFILE_UPDATED: NotificationRule(
        type=NotificationType.ADMIN_MENTOR_PROFILE_UPDATED,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.ADMIN],
        dedupe_key="mentor_id",
        description="Mentor profile update pending admin review.",
    ),
    NotificationType.ADMIN_RISK_ALERT: NotificationRule(
        type=NotificationType.ADMIN_RISK_ALERT,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.ADMIN],
        dedupe_key="risk_id",
        description="High-risk user behavior alert.",
    ),
    NotificationType.ADMIN_SLOT_CONFLICT: NotificationRule(
        type=NotificationType.ADMIN_SLOT_CONFLICT,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.ADMIN],
        dedupe_key="metric_key",
        description="Repeated slot conflicts detected.",
    ),
    NotificationType.ADMIN_REFUND_ALERT: NotificationRule(
        type=NotificationType.ADMIN_REFUND_ALERT,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.ADMIN],
        dedupe_key="user_id",
        description="Multiple refunds detected for a user.",
    ),
    NotificationType.ADMIN_MENTOR_LOW_RATING: NotificationRule(
        type=NotificationType.ADMIN_MENTOR_LOW_RATING,
        category=NotificationCategory.ACTION_REQUIRED,
        recipients=[Role.ADMIN],
        dedupe_key="mentor_id",
        description="Mentor received multiple low ratings.",
    ),
    NotificationType.ADMIN_METRIC_ANOMALY: NotificationRule(
        type=NotificationType.ADMIN_METRIC_ANOMALY,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.ADMIN],
        dedupe_key="metric_key",
        description="Operational metric anomaly detected.",
    ),
    NotificationType.ADMIN_PAYMENT_SUCCESS_DROP: NotificationRule(
        type=NotificationType.ADMIN_PAYMENT_SUCCESS_DROP,
        category=NotificationCategory.INFORMATIONAL,
        recipients=[Role.ADMIN],
        dedupe_key="metric_key",
        description="Payment success rate dropped unexpectedly.",
    ),
    NotificationType.SUPERADMIN_SYSTEM_ALERT: NotificationRule(
        type=NotificationType.SUPERADMIN_SYSTEM_ALERT,
        category=NotificationCategory.SYSTEM,
        recipients=[Role.SUPERADMIN],
        dedupe_key="incident_id",
        description="Critical system alert.",
    ),
    NotificationType.SUPERADMIN_SECURITY_ALERT: NotificationRule(
        type=NotificationType.SUPERADMIN_SECURITY_ALERT,
        category=NotificationCategory.SYSTEM,
        recipients=[Role.SUPERADMIN],
        dedupe_key="incident_id",
        description="Security alert requiring superadmin attention.",
    ),
    NotificationType.SUPERADMIN_RULE_CHANGE: NotificationRule(
        type=NotificationType.SUPERADMIN_RULE_CHANGE,
        category=NotificationCategory.SYSTEM,
        recipients=[Role.SUPERADMIN],
        dedupe_key="change_id",
        description="Rule or configuration change applied.",
    ),
}


BUSINESS_EVENTS = {
    NotificationType.APPOINTMENT_PAYMENT_SUCCESS,
    NotificationType.APPOINTMENT_PAYMENT_FAILED,
    NotificationType.APPOINTMENT_CANCELLED,
    NotificationType.APPOINTMENT_CONFIRMED,
    NotificationType.APPOINTMENT_REJECTED,
    NotificationType.APPOINTMENT_EXPIRED,
    NotificationType.APPOINTMENT_REVIEW_REMINDER,
    NotificationType.APPOINTMENT_RESCHEDULED,
    NotificationType.MENTOR_SUBMITTED_FEEDBACK,
    NotificationType.UPCOMING_APPOINTMENT_REMINDER,
    NotificationType.MENTOR_APPLICATION_SUBMITTED,
    NotificationType.MENTOR_APPLICATION_APPROVED,
    NotificationType.MENTOR_APPLICATION_REJECTED,
    NotificationType.RESUME_UPLOADED,
    NotificationType.SUPPORT_TICKET_CREATED,
    NotificationType.STAFF_APPOINTMENT_CANCELLED,
    NotificationType.STAFF_PAYMENT_FAILED,
    NotificationType.STAFF_USER_FEEDBACK_SUBMITTED,
    NotificationType.STAFF_USER_REPORTED,
    NotificationType.STAFF_CHAT_NO_RESPONSE,
    NotificationType.STAFF_APPOINTMENT_UPCOMING,
    NotificationType.STAFF_MENTOR_NO_CONFIRM,
    NotificationType.STAFF_MENTOR_NO_FEEDBACK,
    NotificationType.STAFF_REPEAT_FAILURE,
    NotificationType.ADMIN_MENTOR_PROFILE_UPDATED,
    NotificationType.ADMIN_RISK_ALERT,
    NotificationType.ADMIN_SLOT_CONFLICT,
    NotificationType.ADMIN_REFUND_ALERT,
    NotificationType.ADMIN_MENTOR_LOW_RATING,
    NotificationType.ADMIN_METRIC_ANOMALY,
    NotificationType.ADMIN_PAYMENT_SUCCESS_DROP,
}

SYSTEM_EVENTS = {
    NotificationType.SYSTEM_ANNOUNCEMENT,
    NotificationType.SUPERADMIN_SYSTEM_ALERT,
    NotificationType.SUPERADMIN_SECURITY_ALERT,
    NotificationType.SUPERADMIN_RULE_CHANGE,
}


def get_notification_rule(notification_type: NotificationType) -> NotificationRule:
    return NOTIFICATION_RULES[notification_type]


def get_db_type(notification_type: NotificationType) -> str:
    return NOTIFICATION_TYPE_MAP[notification_type]


def is_business_event(notification_type: NotificationType) -> bool:
    return notification_type in BUSINESS_EVENTS


def is_system_event(notification_type: NotificationType) -> bool:
    return notification_type in SYSTEM_EVENTS
