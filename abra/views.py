from django.dispatch import receiver
from rest_framework.response import Response
from rest_framework import status, request
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
import jwt
import mongoengine as me
from mongoengine.queryset.visitor import Q
from .models import Message, User
from .serializers import UserSerializer, MessageSerializer
from .jwt import generate_jwt, parse_jwt


def valid_auth_response(user: User):
    data = UserSerializer(user).data
    res = Response(data, status=status.HTTP_200_OK)
    res.set_cookie("jwt", generate_jwt(data), secure=False, httponly=False)
    return res


def check_if_authenticated(request: request.Request):
    try:
        token = request.COOKIES["jwt"]
        parsed = parse_jwt(token)
        return User.objects.get(name=parsed["name"]), None
    except jwt.exceptions.InvalidSignatureError:
        return None, Response(data={"error": "invalid or expired session, try to login again"}, status=status.HTTP_403_FORBIDDEN)
    except KeyError:
        return None, Response(data={"error": "must be authenticated to proceed"}, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@renderer_classes([JSONRenderer])
def signup(request: request.Request):
    try:
        user = User(name=request.data["name"],
                    password=request.data["password"]).signup()
        return valid_auth_response(user=user)
    except KeyError:
        return Response({"error": "please specify name and password"}, status=status.HTTP_400_BAD_REQUEST)
    except me.errors.NotUniqueError:
        return Response({"error": "name already taken, try another one"}, status=status.HTTP_400_BAD_REQUEST)
    except me.errors.ValidationError:
        return Response({"error": "name and password can't be empty"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@renderer_classes([JSONRenderer])
def login(request: request.Request):
    try:
        user = User.objects.get(name=request.data["name"]).login(
            request.data["password"])
        return valid_auth_response(user=user)
    except KeyError:
        return Response(data={"error": "please specify name and password"}, status=status.HTTP_403_FORBIDDEN)
    except me.errors.DoesNotExist:
        return Response(data={"error": "invalid credentials"}, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@renderer_classes([JSONRenderer])
def send_message(request: request.Request):
    try:
        user, res = check_if_authenticated(request=request)
        if res is not None:
            return res
        receiver = User.objects.get(name=request.data["receiver"])
        message = Message(sender=user, receiver=receiver,
                          message=request.data["message"], subject=request.data["subject"]).send()
        data = MessageSerializer(message).data
        return Response(data=data, status=status.HTTP_200_OK)
    except KeyError:
        return Response(data={"error": "please provide receiver name, subject and message"}, status=status.HTTP_400_BAD_REQUEST)
    except me.errors.DoesNotExist:
        return Response(data={"error": "receiver does not exist"}, status=status.HTTP_400_BAD_REQUEST)
    except me.errors.ValidationError:
        return Response(data={"error": "subject and message body can't be empty"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def get_messages(request: request.Request):
    user, res = check_if_authenticated(request=request)
    if res is not None:
        return res
    sent_messages = Message.objects(sender=user.id).order_by(
        "+receiver", "+creation_date")
    received_messages = Message.objects(
        receiver=user.id).order_by("+sender", "+creation_date")
    data = {
        "sent messages": MessageSerializer(sent_messages, many=True).data,
        "received messages": MessageSerializer(received_messages, many=True).data
    }
    received_messages.update(set__readed=True)
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def get_unreaded_messages(request: request.Request):
    user, res = check_if_authenticated(request=request)
    if res is not None:
        return res
    messages = Message.objects(Q(receiver=user.id) &
                               Q(readed=False)).order_by("creation_date")
    data = MessageSerializer(messages, many=True).data
    messages.update(set__readed=True)
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@renderer_classes([JSONRenderer])
def delete_message(request: request.Request, id):
    try:
        user, res = check_if_authenticated(request=request)
        if res is not None:
            return res
        message = Message.objects.get(Q(id=id)
                                      & (Q(receiver=user.id) | Q(sender=user.id)))
        message.delete()
        return Response(data="deleted successfully", status=status.HTTP_204_NO_CONTENT)
    except me.errors.ValidationError:
        return Response(data={"error": "invalid id"}, status=status.HTTP_400_BAD_REQUEST)
    except me.errors.DoesNotExist:
        return Response(data={"error": "message not found, are you sure you are the sender/receiver?"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def get_message(request: request.Request, id):
    try:
        user, res = check_if_authenticated(request=request)
        if res is not None:
            return res
        message = Message.objects.get((Q(receiver=user.id) | Q(sender=user.id)) &
                                      Q(id=id))
        if not message.readed and message.receiver == user:
            message.update(set__readed=True)
        data = MessageSerializer(message).data
        return Response(data=data, status=status.HTTP_200_OK)
    except me.errors.ValidationError:
        return Response(data={"error": "invalid id"}, status=status.HTTP_400_BAD_REQUEST)
    except me.errors.DoesNotExist:
        return Response(data={"error": "message not found, are you sure you are the sender/receiver?"}, status=status.HTTP_400_BAD_REQUEST)
