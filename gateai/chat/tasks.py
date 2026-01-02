from celery import shared_task
from django.utils import timezone

from chat.models import ChatRoom, Message
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import NotificationType
from django.contrib.auth import get_user_model


@shared_task
def notify_staff_unanswered_chats(hours_without_reply: int = 24) -> int:
    """Notify staff when mentors have not replied within a time window."""
    cutoff = timezone.now() - timezone.timedelta(hours=hours_without_reply)
    staff_users = get_user_model().objects.filter(role="staff")
    if not staff_users.exists():
        return 0

    notified = 0
    rooms = ChatRoom.objects.select_related("user", "mentor").all()
    for room in rooms:
        last_message = Message.objects.filter(chat_room=room).order_by("-created_at").first()
        if not last_message:
            continue
        if last_message.sender_id != room.user_id:
            continue
        if last_message.created_at > cutoff:
            continue

        for staff_user in staff_users:
            notify(
                NotificationType.STAFF_CHAT_NO_RESPONSE,
                context={
                    "conversation_id": room.id,
                    "staff": staff_user,
                },
                title="Chat reply overdue",
                message=(
                    f"Mentor {room.mentor.get_full_name() or room.mentor.username} "
                    f"has not replied to {room.user.get_full_name() or room.user.username} "
                    f"in over {hours_without_reply} hours."
                ),
                priority="high",
                payload={"conversation_id": room.id},
            )
            notified += 1

    return notified
