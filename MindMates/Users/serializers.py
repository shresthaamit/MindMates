from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField(required=True)
        self.fields.pop('username', None)

    def validate(self, attrs):
        email = attrs.pop('email')
        password = attrs.pop('password')
        
        user = User.objects.filter(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'username': user.username
            }
        raise serializers.ValidationError("Invalid credentials")
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
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'first_name', 'last_name', 'password', 'old_password', 'date_joined','profile']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':  # Remove `old_password` in POST requests
            self.fields.pop('old_password', None)
    def validate_email(self, value):
        request = self.context.get('request')
        
        # Only check for duplicates during registration (POST request)
        if request and request.method == 'POST':
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value
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