from .models import Community, CommunityMessage
from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model =User
        fields = ['name', 'email']
        
        
