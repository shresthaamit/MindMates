from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    old_password = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(read_only=True)
    def update(self,data):
        request_method = self.context['request'].method
        password  = data.get('password',None)
        if request_method == 'POST':
            if password ==None:
                raise serializers.ValidationError({'password': 'Password is required'})
        elif request_method == 'PUT' or request_method == 'PATCH':
            old_password = data.get('old_password',None)
            if password !=None and old_password == None:
                raise serializers.ValidationError({'old_password': 'Old password is required'})
        return data
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        try:
            user = instance
            password = validated_data.pop("password")
            old_password = validated_data.pop("old_password")
            if user.check_password(old_password):
                user.set_password(password)
                
            else:
                raise Exception("Old password is invalid")
            user.save()
        except Exception as err:
            raise serializers.ValidationError({"info":err})
        
        return super(UserSerializer,self).update(instance,validated_data)
    class Meta:
        model = User
        fields = ['url','id','username','email','first_name','last_name','password','old_password']