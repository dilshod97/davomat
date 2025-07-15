from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, AttendanceViewSet, RegionListAPIView, DistrictListAPIView, MinistryTreeListAPIView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
    path('region/', RegionListAPIView.as_view(), name='region-list'),
    path('district/', DistrictListAPIView.as_view(), name='district-list'),
    path('ministry/', MinistryTreeListAPIView.as_view(), name='ministry-list'),

]
