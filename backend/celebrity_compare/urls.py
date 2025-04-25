from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CelebrityViewSet, FaceCompareAPIView, CrawlCelebritiesAPIView, ComparisonResultDetailAPIView

# 创建路由器并注册viewsets
router = DefaultRouter()
router.register(r'celebrities', CelebrityViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('compare/', FaceCompareAPIView.as_view(), name='face-compare'),
    # 添加获取单个比对结果的API端点
    path('compare/<int:pk>/', ComparisonResultDetailAPIView.as_view(), name='comparison-detail'),
    path('crawl/', CrawlCelebritiesAPIView.as_view(), name='crawl-celebrities'),
]