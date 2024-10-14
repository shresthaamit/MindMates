from django.db import models
from Users.models import UserProfile
from django.contrib.auth.models import User
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
        if user in self.upvotes.all():
            self.upvotes.remove(user)
            self.upvote_count -= 1
            message = 'Upvote removed'
        else:
            if user in self.downvotes.all():
                self.downvotes.remove(user)
                self.downvote_count -= 1
            self.upvotes.add(user)
            self.upvote_count += 1
            message = 'Question upvoted'
        self.save()
        return message

    def toggle_downvote(self, user):
        if user in self.downvotes.all():
            self.downvotes.remove(user)
            self.downvote_count -= 1
            message = 'Downvote removed'
        else:
            if user in self.upvotes.all():
                self.upvotes.remove(user)
                self.upvote_count -= 1
            self.downvotes.add(user)
            self.downvote_count += 1
            message = 'Question downvoted'
        self.save()
        return message
    
    
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
    
    class Meta:
        unique_together = ('user', 'question')
    def __str__(self):
        return f"Answer by {self.user} on {self.question}"

    def add_upvote(self, user):
        if user in self.downvotes.all():
            self.downvotes.remove(user)
        self.upvotes.add(user)

    def add_downvote(self, user):
        if user in self.upvotes.all():
            self.upvotes.remove(user)
        self.downvotes.add(user)
    

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
        