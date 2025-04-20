from .models import Community, CommunityMessage
from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model =User
        fields = ['id', 'username', 'email',]
        
        
class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields =['id','name','description','image']
        extra_kwargs = {
            'creaters':{'read_only':True}
        }
    def create(self, validated_data):
        community = Community.objects.create(
            creaters =self.context['request'].user, **validated_data
        )
        community.members.add(self.context['request'].user)
        return community
        
        
