from rest_framework import serializers
from api.models import User, Group, Agent, Event


class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password']

class AgentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['id', 'name', 'user', 'address', 'status', 'env', 'version']

class EventModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'user', 'level', 'data', 'agent', 'arquivado']
