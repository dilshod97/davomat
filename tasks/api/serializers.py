from rest_framework import serializers
from ..models import Task, Attendance


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
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
