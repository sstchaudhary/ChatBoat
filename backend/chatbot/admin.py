from django.contrib import admin
from .models import Document, ChatHistory


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'size', 'indexed', 'uploaded_at']
    list_filter = ['indexed', 'file_type']
    search_fields = ['name']
    readonly_fields = ['uploaded_at']


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['question', 'asked_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['asked_at']
