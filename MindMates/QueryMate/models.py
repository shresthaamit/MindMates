from django.db import models
from Users.models import UserProfile
from django.contrib.auth.models import User
from django.db.models import F
# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name
    
    
class Question(models.Model):
    image = models.ImageField(upload_to='questions/images/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.ManyToManyField(Tag,related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    upvotes = models.ManyToManyField(User, related_name='upvoted_questions', blank=True)
    downvotes = models.ManyToManyField(User, related_name='downvoted_questions', blank=True)
    upvote_count = models.PositiveIntegerField(default=0)  # Upvote count
    downvote_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def toggle_upvote(self, user):
        if self.upvotes.filter(id=user.id).exists():
            self.upvotes.remove(user)
            self.upvote_count = F('upvote_count') - 1
            message = 'Upvote removed'
        else:
            if self.downvotes.filter(id=user.id).exists():
                self.downvotes.remove(user)
                self.downvote_count = F('downvote_count') - 1
            self.upvotes.add(user)
            self.upvote_count = F('upvote_count') + 1
            message = 'Question upvoted'

        self.save(update_fields=['upvote_count', 'downvote_count'])
        self.refresh_from_db(fields=['upvote_count', 'downvote_count'])

        return {
            "status": message,
            "upvote_count": self.upvote_count,
            "downvote_count": self.downvote_count
        }

    def toggle_downvote(self, user):
        if self.downvotes.filter(id=user.id).exists():
            self.downvotes.remove(user)
            self.downvote_count = F('downvote_count') - 1
            message = 'Downvote removed'
        else:
            if self.upvotes.filter(id=user.id).exists():
                self.upvotes.remove(user)
                self.upvote_count = F('upvote_count') - 1
            self.downvotes.add(user)
            self.downvote_count = F('downvote_count') + 1
            message = 'Question downvoted'

        self.save(update_fields=['upvote_count', 'downvote_count'])
        self.refresh_from_db(fields=['upvote_count', 'downvote_count'])

        return {
            "status": message,
            "upvote_count": self.upvote_count,
            "downvote_count": self.downvote_count
        }
    
class Answer(models.Model):
    image  =  models.ImageField(upload_to='answers/images/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='answer')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer')
    answerurl =  models.URLField(blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    upvotes = models.ManyToManyField(User, related_name='upvoted_answers', blank=True)
    downvotes = models.ManyToManyField(User, related_name='downvoted_answers', blank=True)
    upvote_count = models.PositiveIntegerField(default=0)  # Upvote count
    downvote_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'question')
    def __str__(self):
        return f"Answer by {self.user} on {self.question}"

    def toggle_upvote(self, user):
        if self.upvotes.filter(id=user.id).exists():
            # Already upvoted — remove it
            self.upvotes.remove(user)
            self.upvote_count = max(0, self.upvote_count - 1)
            message = 'Upvote removed'
        else:
            # Remove downvote if present
            if self.downvotes.filter(id=user.id).exists():
                self.downvotes.remove(user)
                self.downvote_count = max(0, self.downvote_count - 1)
            # Add upvote
            self.upvotes.add(user)
            self.upvote_count += 1
            message = 'Answer upvoted'
        self.save()
        return message

    def toggle_downvote(self, user):
        if self.downvotes.filter(id=user.id).exists():
            # Already downvoted — remove it
            self.downvotes.remove(user)
            self.downvote_count = max(0, self.downvote_count - 1)
            message = 'Downvote removed'
        else:
            # Remove upvote if present
            if self.upvotes.filter(id=user.id).exists():
                self.upvotes.remove(user)
                self.upvote_count = max(0, self.upvote_count - 1)
            # Add downvote
            self.downvotes.add(user)
            self.downvote_count += 1
            message = 'Answer downvoted'
        self.save()
        return message
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='review_answers')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    # class Meta:
    def __str__(self):
        return f"Review by {self.user} on {self.answer}"
        