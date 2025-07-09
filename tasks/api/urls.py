from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, AttendanceViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
]
