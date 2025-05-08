from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentUploadView, 
    ContentGenerationView, 
    GeneratedContentViewSet,
    AvailableModelsView,
    MedicalStandardView,
    StandardSearchView,
    StandardTypeViewSet
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
    path('standards/search/', StandardSearchView.as_view(), name='standard-search'),
    path('', include(router.urls)), # Include ViewSet URLs
]
