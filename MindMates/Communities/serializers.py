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
        fields = ['id','name','description','creaters','member','member_count','created_at','image','is_member']
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
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    class Meta:
        model = CommunityMessage
        fields = ['id','community','community_id','sender','sender_id','content','file', 'created_at', 'is_edited', 'is_deleted','like_count', 'is_liked']
        read_only_fields = ['created_at', 'is_edited', 'is_deleted']
    def get_is_liked(self, obj):
        request = self.context.get('request')
        return request and request.user.is_authenticated and request.user in obj.likes.all()
    def create(self, validated_data):
        validated_data.pop('sender_id', None)
        validated_data.pop('community_id', None)
        return super().create(validated_data)
class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        required=False,  # Make file optional
        allow_null=True,
        style={'input_type': 'file', 'template': 'rest_framework/file.html'}
    )
    content = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = CommunityMessage
        fields = ['content', 'file']
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def validate(self, data):
        # Require either content or file
        if not data.get('content') and not data.get('file'):
            raise serializers.ValidationError("Either content or file must be provided")
        return data