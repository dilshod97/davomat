from rest_framework import serializers
from ..models import Task, Attendance, Region, District, MinistryTree


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
        queryset=Region.objects.all(), write_only=True, source='region'
    )

    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), write_only=True, source='district'
    )
    ministry = MinistryTreeSerializer(read_only=True)
    ministry_id = serializers.PrimaryKeyRelatedField(
        queryset=MinistryTree.objects.all(), write_only=True, source='ministry'
    )

    class Meta:
        model = Task
        fields = ['id', 'task', 'start_date', 'end_date', 'created_at',
                  'region', 'region_id', 'district', 'district_id', 'ministry', 'ministry_id']
        read_only_fields = ['user']


class AttendanceSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), many=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        tasks = validated_data.pop('task', [])
        attendance = Attendance.objects.create(**validated_data)
        attendance.task.set(tasks)  # ManyToMany bog'lash
        return attendance
