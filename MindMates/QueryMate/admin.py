from django.contrib import admin
from .models import Tag, Question
# Register your models here.
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at', 'user')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)