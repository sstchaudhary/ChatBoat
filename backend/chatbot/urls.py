from django.urls import path
from .views import DocumentView, DocumentDeleteView, AskView, AskStreamView, ChatHistoryView, HealthView, DebugDocumentsView, ClearVectorstoreView

urlpatterns = [
    path('documents/', DocumentView.as_view()),
    path('documents/<int:doc_id>/', DocumentDeleteView.as_view()),
    path('ask/', AskView.as_view()),
    path('ask/stream/', AskStreamView.as_view()),
    path('history/', ChatHistoryView.as_view()),
    path('health/', HealthView.as_view()),
    path('debug/documents/', DebugDocumentsView.as_view()),
    path('debug/clear-vectorstore/', ClearVectorstoreView.as_view()),
]
