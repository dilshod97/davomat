from rest_framework import serializers
from ..models import Task, Attendance, Region, District, MinistryTree, NewsMedia, News, Reminder, Distance
import math


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


class MinistryTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinistryTree
        fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name_uz', 'name_ru', 'name_cr', 'name_en']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name_uz', 'name_ru', 'name_cr', 'pid', 'region']


class TaskSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), write_only=True, source='region', required=False, allow_null=True
    )

    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), write_only=True, source='district', required=False, allow_null=True
    )

    ministry = MinistryTreeSerializer(read_only=True)
    ministry_id = serializers.PrimaryKeyRelatedField(
        queryset=MinistryTree.objects.all(), write_only=True, source='ministry', required=False, allow_null=True
    )

    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = Task
        fields = [
            'id', 'task', 'start_date', 'end_date', 'created_at',
            'region', 'region_id', 'district', 'district_id', 'ministry', 'ministry_id', 'is_active'
        ]
        read_only_fields = ['user', 'created_at']


class AttendanceSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), many=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        tasks = validated_data.pop('task', [])
        attendance = Attendance.objects.create(**validated_data)

        for i in tasks:
            ministry_lat = i.ministry.latitude
            ministry_lng = i.ministry.longitude

            user_lat = attendance.latitude
            user_lng = attendance.longitude
            distance = haversine(user_lat, user_lng, ministry_lat, ministry_lng)
            Distance.objects.create(attendance=attendance, distance=distance)

        attendance.task.set(tasks)
        return attendance


class LastAttendanceSerializer(serializers.ModelSerializer):
    task = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'user', 'latitude', 'longitude', 'task', 'task_description', 'timestamp', 'created_at']

    def get_task(self, obj):
        tasks = obj.task.filter(is_deleted=False)
        return TaskSerializer(tasks, many=True).data


class NewsMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsMedia
        fields = ["id", "media_type", "file", "url"]


class NewsSerializer(serializers.ModelSerializer):
    media = NewsMediaSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = ["id", "document_type", "title", "summary", "link", "media", "created_at", "updated_at"]


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = "__all__"
