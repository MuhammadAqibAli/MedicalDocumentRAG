from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentUploadView, 
    ContentGenerationView, 
    GeneratedContentViewSet,
    AvailableModelsView
)

router = DefaultRouter()
router.register(r'generated-content', GeneratedContentViewSet, basename='generatedcontent')
# You could add a ViewSet for Documents if you need list/retrieve for uploaded docs

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('generate/', ContentGenerationView.as_view(), name='content-generation'),
    path('models/', AvailableModelsView.as_view(), name='available-models'),
    path('', include(router.urls)), # Include ViewSet URLs
]
