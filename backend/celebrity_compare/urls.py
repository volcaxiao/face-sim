from django.urls import path, include
from rest_framework import routers
from .views import (
    CelebrityViewSet, 
    FaceCompareAPIView, 
    ComparisonResultDetailAPIView,
    ComparisonStatusAPIView,
    CrawlCelebritiesAPIView,
    ComparisonHistoryAPIView,
    ShareComparisonAPIView
)

router = routers.DefaultRouter()
router.register('celebrities', CelebrityViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('compare/', FaceCompareAPIView.as_view(), name='face-compare'),
    path('compare/<uuid:pk>/', ComparisonResultDetailAPIView.as_view(), name='comparison-detail'),
    path('compare/status/<uuid:pk>/', ComparisonStatusAPIView.as_view(), name='comparison-status'),
    path('compare/history/', ComparisonHistoryAPIView.as_view(), name='comparison-history'),
    path('compare/share/<uuid:pk>/', ShareComparisonAPIView.as_view(), name='share-comparison'),
    path('admin/crawl-celebrities/', CrawlCelebritiesAPIView.as_view(), name='crawl-celebrities'),
]