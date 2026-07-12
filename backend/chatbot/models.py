from django.db import models


class Document(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='docs/')
    file_type = models.CharField(max_length=10)
    size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    indexed = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ChatHistory(models.Model):
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list)
    asked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question[:50]

    class Meta:
        verbose_name_plural = 'Chat Histories'
