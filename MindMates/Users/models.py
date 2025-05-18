from typing import Any
from django.db import models
from django.contrib.auth.models import User
import os
from django.utils.deconstruct import deconstructible
# Create your models here.
@deconstructible
class GenerateProfileImagePath(object):
    def __init__(self):
        pass
    
    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        path = f'accounts/{instance.user.id}/images/'
        name = f'profile_image.{ext}'
        return os.path.join(path, name)
USER_PROFILE_IMAGE_PATH = GenerateProfileImagePath()
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.FileField(upload_to=USER_PROFILE_IMAGE_PATH, blank=True, null=True)
    
    
    def __str__(self):
        return self.user.username