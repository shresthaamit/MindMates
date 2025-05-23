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
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_url = models.URLField(blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    likes = models.ManyToManyField(
        User, 
        related_name='liked_messages',
        blank=True
    )
    like_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
    def update_like_count(self):
        """Updates the cached like count"""
        self.like_count = self.likes.count()
        self.save(update_fields=['like_count'])
    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}..."