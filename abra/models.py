import mongoengine as me
from django.contrib.auth.hashers import check_password, make_password
from .settings import SALT
from django.utils import timezone


class User(me.Document):
    name = me.StringField(min_length=1, max_length=200, unique=True)
    password = me.StringField(max_length=200)

    def __set_password(self):
        if len(self.password.replace(" ","")) == 0:
            raise me.errors.ValidationError()
        self.password = make_password(
            password=self.password, salt=SALT)
        self.save()
        return self

    def compare_passwords(self, raw_password):
        return check_password(password=raw_password, encoded=self.password)

    def signup(self):
        self.__set_password()
        return self

    def login(self, password):
        if check_password(password=password, encoded=self.password):
            return self
        else:
            raise me.errors.DoesNotExist()

    def __str__(self):
        return f"name: {self.name}, password: {self.password}"


class Message(me.Document):
    sender = me.ReferenceField(document_type=User, required=True)
    receiver = me.ReferenceField(document_type=User, required=True)
    subject = me.StringField(min_length=1, required=True)
    message = me.StringField(min_length=1, required=True)
    creation_date = me.DateTimeField(default=timezone.now, required=True)
    readed = me.BooleanField(default=False, required=True)

    def send(self):
        self.save()
        return self

    def __str__(self):
        return f"sender: {self.sender},\n receiver: {self.receiver},\n subject: {self.subject}, message: {self.message}, creation_date: {self.creation_date}, readed: {self.readed}"
