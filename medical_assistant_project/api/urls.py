from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentUploadView,
    ContentGenerationView,
    GeneratedContentViewSet,
    AvailableModelsView,
    MedicalStandardView,
    StandardSearchView,
    StandardTypeViewSet,
    MedicalStandardCompareView,
    DocumentDownloadView,
    AuditQuestionGeneratorView,
    AuditQuestionUpdateView,
    AuditQuestionDeleteView,
    AuditQuestionListView,
    ComplaintView,
    PracticeViewSet,
    FeedbackMethodViewSet,
    FeedbackViewSet,
    FeedbackAttachmentDownloadView,
    UserListView,
    SimpleChatbotMessageView,
    SimpleChatbotConversationView,
    SimpleChatbotHealthView
)

router = DefaultRouter()
router.register(r'generated-content', GeneratedContentViewSet, basename='generatedcontent')
router.register(r'standard-types', StandardTypeViewSet, basename='standardtype')
router.register(r'practices', PracticeViewSet, basename='practice')
router.register(r'feedback-methods', FeedbackMethodViewSet, basename='feedbackmethod')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
# Simple chatbot doesn't use viewsets

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('generate/', ContentGenerationView.as_view(), name='content-generation'),
    path('models/', AvailableModelsView.as_view(), name='available-models'),
    path('standards/', MedicalStandardView.as_view(), name='standards-list-create'),
    path('standards/<uuid:standard_id>/', MedicalStandardView.as_view(), name='standard-detail'),
    path('standards/compare/', MedicalStandardCompareView.as_view(), name='standards-compare'),
    path('standards/search/', StandardSearchView.as_view(), name='standard-search'),
    path('', include(router.urls)), # Include ViewSet URLs
    # Document management endpoints
    path('documents/', DocumentUploadView.as_view(), name='document-list'),
    path('documents/<uuid:document_id>/', DocumentUploadView.as_view(), name='document-detail'),
    path('documents/<uuid:document_id>/download/', DocumentDownloadView.as_view(), name='document-download'),

    # Audit question endpoints
    path('audit-questions/', AuditQuestionListView.as_view(), name='audit-question-list'),
    path('audit-questions/generate/', AuditQuestionGeneratorView.as_view(), name='audit-question-generate'),
    path('audit-questions/<uuid:question_id>/', AuditQuestionUpdateView.as_view(), name='audit-question-update'),
    path('audit-questions/<uuid:question_id>/delete/', AuditQuestionDeleteView.as_view(), name='audit-question-delete'),

    # Complaint endpoints
    path('complaints/', ComplaintView.as_view(), name='complaint-list-create'),
    path('complaints/<uuid:complaint_id>/', ComplaintView.as_view(), name='complaint-detail'),

    # Feedback attachment download endpoint
    path('feedback-attachments/<uuid:attachment_id>/download/', FeedbackAttachmentDownloadView.as_view(), name='feedback-attachment-download'),

    # Simple Chatbot endpoints
    path('chatbot/message/', SimpleChatbotMessageView.as_view(), name='simple-chatbot-message'),
    path('chatbot/conversations/', SimpleChatbotConversationView.as_view(), name='simple-chatbot-conversations'),
    path('chatbot/conversations/<str:session_id>/', SimpleChatbotConversationView.as_view(), name='simple-chatbot-conversation-detail'),
    path('chatbot/health/', SimpleChatbotHealthView.as_view(), name='simple-chatbot-health'),

    # User management endpoint
    path('users/', UserListView.as_view(), name='user-list'),
]
