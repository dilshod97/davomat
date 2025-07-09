from rest_framework import serializers
from ..models import User


class UserSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'middle_name', 'birth_date',
            'phone', 'chat_id', 'img', 'organization', 'position', 'lavozim',
            'sector', 'sector_name', 'profiles'
        )
