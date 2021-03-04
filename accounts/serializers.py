from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer class for User object"""

    class Meta:
        model = User
        fields = ('username', 'password', 'phone', 'address', 'gender',
                  'age', 'description', 'first_name', 'last_name', 'email')
        extra_kwargs = {"password": {'write_only': True}}

    def create(self, validated_data):
        """Create user with hashed password"""
        return User.objects.create_user(**validated_data)
