# from rest_framework import serializers
# from .models import Tag, Question
# class TagSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Tag
#         fields = ('id', 'name')
        
# class QuestionSerializer(serializers.ModelSerializer):
#     tags = TagSerializer(many=True,read_only=True)
#     tag_ids = serializers.PrimaryKeyRelatedField(queryset = Tag.objects.all(), write_only=True, many=True,source='tags')
#     user  =  serializers.StringRelatedField(read_only=True)
#     upvote_count = serializers.SerializerMethodField()
#     downvote_count   = serializers.SerializerMethodField()
    
    
#     class Meta:
#         model = Question
#         fields = [
#             'id', 'title', 'description', 'image', 'user', 
#             'created_at', 'updated_at', 'upvotes', 'downvotes', 
#             'tags', 'tag_ids', 'upvote_count', 'downvote_count'
#         ]
#         readonly = ['user', 'created_at', 'updated_at', 'upvotes','downvotes']
        
#     def get_upvote_counts(self, obj):
#         return obj.upvotes.count()
    
#     def get_downvote_counts(self, obj):
#         return obj.downvotes.count()
    
#     def create(self, validated_data):
#         tags = validated_data.pop('tags', [])
#         question = Question.objects.create(**validated_data)
#         question.tags.set(tags)  # Set many-to-many relationship using .set()
#         return question
    
#     def update(self, instance, validated_data):
#         tags = validated_data.pop('tags', [])
#         question = super().update(instance, validated_data)
#         if tags:
#             question.tags.set(tags)  # Use .set() for many-to-many relationship
#         return question
from rest_framework import serializers
from .models import Tag, Question,Answer,Review

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    answer = serializers.PrimaryKeyRelatedField(read_only=True)
    question_id = serializers.SerializerMethodField()
    question_title = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    class Meta:
        model = Review
        fields = ['id', 'content', 'user', 'answer', 'question_id', 'question_title','is_owner']
        extra_kwargs = {
            'content': {'required': True},
        }
    def get_question_id(self, obj):
        return obj.answer.question.id if obj.answer and obj.answer.question else None

    def get_question_title(self, obj):
        return obj.answer.question.title if obj.answer and obj.answer.question else None
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.user == request.user
        return False

class AnswerSerializer(serializers.ModelSerializer):
    review_answers = ReviewSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Answer
        fields = ['id', 'user', 'content','image', 'created_at', 'updated_at','review_answers','upvote_count','downvote_count']
        read_only_fields = ['user', 'created_at', 'updated_at']
        
        
    def validate(self, data):
        user =  self.context['request'].user
        question = self.context.get('question') 
       
        if Answer.objects.filter(user=user,question=question).exists():
            raise serializers.ValidationError('You have already answered this question')
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class QuestionSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer(many=True,read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), write_only=True, many=True, source='tags')
    user = serializers.StringRelatedField(read_only=True)
    is_owner = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        
        model = Question
        fields = [
            'id', 'title', 'description', 'image', 'user', 'answer', 'user_email',
            'created_at', 'updated_at', 'tags', 'tag_ids','upvote_count','downvote_count','is_owner'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at','is_owner']
    def get_is_owner(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, "user"):
            return obj.user == request.user
        return False   
        
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        question = Question.objects.create(**validated_data)
        question.tags.set(tags)
        return question

class VoteSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['upvote', 'downvote'])
