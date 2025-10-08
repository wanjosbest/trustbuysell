from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def last_message(self):
        return self.messages.order_by('-timestamp').first()

    def other_user(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def __str__(self):
        users = ", ".join([u.username for u in self.participants.all()])
        return f"Chat between {users}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
