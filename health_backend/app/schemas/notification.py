from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.notification import NotificationChannel, NotificationType
from app.schemas.common import BaseSchema


class NotificationRead(BaseSchema):
    id: UUID
    user_id: UUID
    type: NotificationType
    channel: NotificationChannel
    title: str
    body: Optional[str]
    is_read: bool
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime
