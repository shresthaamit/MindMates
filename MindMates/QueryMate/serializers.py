from rest_framework import serializers
from .models import Tag, Question
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
        
class QuestionSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True,read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(queryset = Tag.objects.all(), many=True,source='tags')
    user  =  serializers.StringRelatedField(read_only=True)
    upvote_counts = serializers.SerializerMethodField()
    downvote_counts = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Question
        fields = [
            'id', 'title', 'description', 'image', 'user', 
            'created_at', 'updated_at', 'upvotes', 'downvotes', 
            'tags', 'tag_ids', 'upvote_counts', 'downvote_counts'
        ]
        readonly = ['user', 'created_at', 'updated_at', 'upvotes','downvotes']
        
    def get_upvote_count(self, obj):
        return obj.upvotes.count()
    
    def get_downvote_count(self, obj):
        return obj.downvotes.count()
    
    def create(self, validate_data):
        tags = validate_data.pop('tags',[])
        question = Question.objects.create(**validate_data)
        question.tags.set(tags)
        return question
    
    def update(self, validate_data):
        tags = validate_data.pop('tags',[])
        question = super().update(validate_data)
        question.tags.set(tags)
        return question
                                          