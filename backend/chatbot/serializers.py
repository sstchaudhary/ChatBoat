from rest_framework import serializers
from .models import Document, ChatHistory


class DocumentSerializer(serializers.ModelSerializer):
    size_kb = serializers.SerializerMethodField()

    def get_size_kb(self, obj):
        return round(obj.size / 1024, 2)

    class Meta:
        model = Document
        fields = ['id', 'name', 'file_type', 'size_kb', 'uploaded_at', 'indexed']


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id', 'question', 'answer', 'sources', 'asked_at']
