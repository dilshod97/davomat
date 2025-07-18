from rest_framework import viewsets
from ..models import Task, Attendance, MinistryTree, District, Region
from .serializers import TaskSerializer, AttendanceSerializer, RegionSerializer, DistrictSerializer
from rest_framework.permissions import IsAuthenticated
from datetime import date
from rest_framework import generics
from django.db.models import Q
from .serializers import MinistryTreeSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, end_date__gte=date.today())


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Attendance.objects.filter(user=self.request.user)


class MinistryTreeListAPIView(generics.ListAPIView):
    queryset = MinistryTree.objects.all()
    serializer_class = MinistryTreeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(name__icontains=name) |
                Q(soha__icontains=name) |
                Q(katta_otasi__icontains=name) |
                Q(daraja__icontains=name)
            )
        return queryset


class RegionListAPIView(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

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
        return queryset


class DistrictListAPIView(generics.ListAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(name_uz__icontains=name) |
                Q(name_ru__icontains=name) |
                Q(name_cr__icontains=name)
            )
        return queryset
