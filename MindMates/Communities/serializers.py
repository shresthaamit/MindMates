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
        
class CommunityDetailSerializer(serializers.ModelSerializer):
    creaters  = UserSerializer(read_only=True)
    member = UserSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    class Meta:
        model= Community
        fields = ['id','name','description','creaters','members','member_count','created_at','images','is_member']
    def get_member_count(self,obj):
        return obj.members.count()
    
    def get_is_member(self, obj):
        request =self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(id = request.user.id).exists()
        return False
    
class JoinLeaveSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value

class CommunityMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.IntegerField(write_only=True, required =False)
    community_id = serializers.IntegerField(write_only=True, required=False)
    class Meta:
        model = CommunityMessage
        fields = ['id','community','community_id','sender','sender_id','content','file', 'created_at', 'is_edited', 'is_deleted']
        read_only_fields = ['created_at', 'is_edited', 'is_deleted']
        
    def create(self, validated_data):
        validated_data.pop('sender_id', None)
        validated_data.pop('community_id', None)
        return super().create(validated_data)
    
