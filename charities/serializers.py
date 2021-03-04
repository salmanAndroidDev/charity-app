from rest_framework import serializers

from .models import Benefactor
from .models import Charity, Task


class BenefactorSerializer(serializers.ModelSerializer):
    """Serializer class for benefactor object"""
    class Meta:
        model = Benefactor
        fields = ('experience', 'free_time_per_week')


class CharitySerializer(serializers.ModelSerializer):
    """Serializer class for charity object"""
    class Meta:
        model = Charity
        fields = ('name', 'reg_number')


class TaskSerializer(serializers.ModelSerializer):
    """Serializer class for Task object"""
    class Meta:
        model = Task
        fields = ('__all__')
