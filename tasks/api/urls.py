from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, AttendanceViewSet, RegionListAPIView, DistrictListAPIView, MinistryTreeListAPIView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'region', RegionListAPIView, basename='region')
router.register(r'district', DistrictListAPIView, basename='district')
router.register(r'ministry', MinistryTreeListAPIView, basename='ministry')

urlpatterns = [
    path('', include(router.urls)),
]
