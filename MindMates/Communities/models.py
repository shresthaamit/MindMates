from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Community(models.Model):
    name = models.CharField(max_length=100)
    description= models.TextField()
    creaters = models.ForeignKey(User, on_delete=models.CASCADE, related_name='create_communities')
    members = models.ManyToManyField(User,related_name='communities')
    online_members = models.ManyToManyField(User, related_name='online_communities', blank=True)
    created_at= models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='community_image', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class CommunityMessage(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    file = models.FileField(upload_to='community_files/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}..."