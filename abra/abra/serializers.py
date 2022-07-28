from rest_framework_mongoengine import serializers
from .models import Message, User


class UserSerializer(serializers.DocumentSerializer):
    class Meta:
        model = User
        fields = ["id", "name"]

class MessageSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Message
        fields = "__all__"