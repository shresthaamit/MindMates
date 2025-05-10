from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.HyperlinkedRelatedField(read_only=True,many=False,view_name="user-detail")
    class Meta:
        model = UserProfile
        fields = ['url',  'id', 'user', 'profile_picture' ] 
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    old_password = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(read_only=True)    
    profile = UserProfileSerializer(source='userprofile', read_only=True)

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'first_name', 'last_name', 'password', 'old_password', 'profile']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':  # Remove `old_password` in POST requests
            self.fields.pop('old_password', None)

    def validate(self, data):
        request = self.context['request']
        request_method = request.method
        password = data.get('password', None)

        if request_method == 'POST':  # User Registration
            if password is None:
                raise serializers.ValidationError({'password': 'Password is required'})

        elif request_method in ['PUT', 'PATCH']:  # User Update (Change Password)
            if password:  # Only check `old_password` if password update is requested
                old_password = request.data.get('old_password', None)  # Get `old_password` from request data
                if old_password is None:
                    raise serializers.ValidationError({'old_password': 'Old password is required'})
                if not self.instance.check_password(old_password):
                    raise serializers.ValidationError({'old_password': 'Old password is incorrect'})

        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        if password:  # Only process password change if it's included
            old_password = self.context['request'].data.get('old_password', None)  # Fetch from request
            if old_password is None:
                raise serializers.ValidationError({'old_password': 'Old password is required'})
            if not instance.check_password(old_password):
                raise serializers.ValidationError({'old_password': 'Old password is incorrect'})

            instance.set_password(password)

        return super().update(instance, validated_data)