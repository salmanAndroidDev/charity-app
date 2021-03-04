from http.client import HTTPResponse

from django.http import JsonResponse, Http404
from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task
from charities.serializers import (
    TaskSerializer, CharitySerializer, BenefactorSerializer
)


class BenefactorRegistration(generics.CreateAPIView):
    """API view for benefactor object creation"""
    permission_classes = [IsAuthenticated]
    serializer_class = BenefactorSerializer

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


class CharityRegistration(generics.CreateAPIView):
    """API view for charity object creation"""
    permission_classes = [IsAuthenticated]
    serializer_class = CharitySerializer

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)


class TaskRequest(generics.RetrieveAPIView):
    """API View for requesting a task by benefactor"""
    permission_classes = [IsBenefactor]
    serializer_class = TaskSerializer

    def get(self, *args, **kwargs):
        task = get_object_or_404(Task, id=kwargs['task_id'])
        if task.state == 'P':
            task.state = 'W'
            task.assigned_benefactor = self.request.user.benefactor
            task.save()
            data = {'detail': 'Request sent.'}
            self.serializer_class.data = data
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            data = {'detail': 'This task is not pending.'}
            self.serializer_class.data = data
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)


class TaskResponse(APIView):
    """API View for charity object to response benefactor assigned tasks"""
    permission_classes = [IsCharityOwner]

    def post(self, request, **kwargs):
        response = request.data.get('response')
        task = get_object_or_404(Task, id=kwargs['task_id'])
        state = None

        if 'A' != response != 'R':
            data = {'detail': 'Required field ("A" for accepted / "R" for rejected)'}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        elif task.state != 'W':
            data = {'detail': 'This task is not waiting.'}
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)

        elif response == 'A':
            state = 'A'

        elif response == 'R':
            state = 'P'
            task.assigned_benefactor = None

        # if either response is A or R
        task.state = state
        task.save()
        data = {'detail': 'Response sent.'}
        return Response(data=data, status=status.HTTP_200_OK)


class DoneTask(APIView):
    """API View for charity to change state of the task to Done."""
    permission_classes = [IsCharityOwner]
    def post(self, request, **kwargs):
        task = get_object_or_404(Task, id=kwargs['task_id'])

        if task.state != 'A':
            data = {'detail': 'Task is not assigned yet.'}
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)
        else:
            task.state = 'D'
            task.save()
            data = {'detail': 'Task has been done successfully.'}
            return Response(data=data, status=status.HTTP_200_OK)
