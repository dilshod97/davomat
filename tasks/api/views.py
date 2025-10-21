from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Task, Attendance, MinistryTree, District, Region, News, NewsMedia, Reminder
from .serializers import (TaskSerializer, AttendanceSerializer, AttendanceDetailSerializer, RegionSerializer, DistrictSerializer,
                          LastAttendanceSerializer, NewsSerializer, NewsMediaSerializer, ReminderSerializer)
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from datetime import date
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .serializers import MinistryTreeSerializer


class ReportPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ReportPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        base_qs = Task.objects.filter(user=self.request.user)
        if self.action == 'destroy':
            return base_qs
        if self.request.GET.get('all'):
            return Task.objects.filter(user=self.request.user, is_deleted=False).order_by('-created_at')
        return (Task.objects.filter(user=self.request.user, is_deleted=False).
                filter(Q(end_date__gte=date.today()) | (Q(end_date__isnull=True) & Q(is_active=True)))).order_by('-created_at')

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ReportPagination

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return AttendanceDetailSerializer
        return AttendanceSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        subquery = (
            Attendance.objects.filter(user=user)
            .values('user', 'created_at__date')
            .annotate(last_created=Max('created_at'))
        )

        last_records = Attendance.objects.filter(
            user=user,
            created_at__in=[item['last_created'] for item in subquery]
        ).order_by('-created_at')

        return last_records


class MinistryTreeListAPIView(generics.ListAPIView):
    queryset = MinistryTree.objects.all()
    serializer_class = MinistryTreeSerializer
    pagination_class = ReportPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(name__icontains=name) |
                Q(soha__icontains=name) |
                Q(katta_otasi__icontains=name) |
                Q(daraja__icontains=name)
            ).order_by('name')
        return queryset


class RegionListAPIView(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    pagination_class = ReportPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(name_uz__icontains=name) |
                Q(name_ru__icontains=name) |
                Q(name_cr__icontains=name) |
                Q(name_en__icontains=name)
            )
        return queryset.order_by('name_uz')


class DistrictListAPIView(generics.ListAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    pagination_class = ReportPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        region_id = self.request.query_params.get('region_id')
        if name:
            queryset = queryset.filter(
                Q(name_uz__icontains=name) |
                Q(name_ru__icontains=name) |
                Q(name_cr__icontains=name)
            )
        if region_id:
            queryset = queryset.filter(region_id=int(region_id))
        return queryset


class LastAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attendance = Attendance.objects.filter(user=request.user).order_by('-created_at').first()
        if attendance:
            serializer = LastAttendanceSerializer(attendance)
            return Response(serializer.data)
        return Response({'detail': 'Attendance not found'}, status=404)


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer


class NewsMediaViewSet(viewsets.ModelViewSet):
    queryset = NewsMedia.objects.all()
    serializer_class = NewsMediaSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer
