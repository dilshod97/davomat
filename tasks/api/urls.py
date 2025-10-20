from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (TaskViewSet, AttendanceViewSet, RegionListAPIView, DistrictListAPIView, MinistryTreeListAPIView,
                    LastAttendanceView, ReminderViewSet, NewsViewSet, NewsMediaViewSet)
from .report_views import DailyReportView, PeriodReportView, BandlikHisobotAPIView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r"news", NewsViewSet, basename="news")
router.register(r"news-media", NewsMediaViewSet, basename="newsmedia")
router.register(r"reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    path('', include(router.urls)),
    path('region/', RegionListAPIView.as_view(), name='region-list'),
    path('district/', DistrictListAPIView.as_view(), name='district-list'),
    path('ministry/', MinistryTreeListAPIView.as_view(), name='ministry-list'),
    path('last-attendance/', LastAttendanceView.as_view(), name='last-attendance'),
    path('daily-report/', DailyReportView.as_view(), name='DailyReportView'),
    path('period-report/', PeriodReportView.as_view(), name='PeriodReportView'),
    path('day-bandlik/', BandlikHisobotAPIView.as_view(), name='BandlikHisobotAPIView'),

]
