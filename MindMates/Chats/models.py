from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Conversation(models.Model):
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='convo_starter')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='convo_participate')
    created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation between {self.initiator} and {self.receiver}"
    
    
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    file =  models.FileField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']    
    def __str__(self):
        return f"Message from {self.sender} in {self.conversation}"
