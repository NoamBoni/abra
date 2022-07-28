from django.contrib import admin
from django.urls import path
from .views import *


urlpatterns = [
    path('admin', admin.site.urls),
    path('signup', signup),
    path('login', login),
    path("message/send", send_message),
    path("message/all", get_messages),
    path("message/unreaded", get_unreaded_messages),
    path("message/delete/<id>", delete_message),
    path("message/<id>", get_message)
]
