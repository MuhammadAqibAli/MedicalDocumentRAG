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
    AuditQuestionDeleteView
)

router = DefaultRouter()
router.register(r'generated-content', GeneratedContentViewSet, basename='generatedcontent')
router.register(r'standard-types', StandardTypeViewSet, basename='standardtype')

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
    path('audit-questions/generate/', AuditQuestionGeneratorView.as_view(), name='audit-question-generate'),
    path('audit-questions/<uuid:question_id>/', AuditQuestionUpdateView.as_view(), name='audit-question-update'),
    path('audit-questions/<uuid:question_id>/delete/', AuditQuestionDeleteView.as_view(), name='audit-question-delete'),
]
