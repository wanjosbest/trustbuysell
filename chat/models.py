from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Chat(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def last_message(self):
        """Return the most recent message for the chat."""
        return self.messages.order_by('-timestamp').first()

    def other_user(self, current_user):
        """Return the other participant in the chat."""
        return self.participants.exclude(id=current_user.id).first()

    def __str__(self):
        users = ", ".join([u.username for u in self.participants.all()])
        return f"Chat between {users}"



class Message(models.Model):
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
