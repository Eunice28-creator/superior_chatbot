from django.urls import path
from .views import superior_chat, health_check

app_name = "chatbot"  # Define the app namespace

urlpatterns = [
    path("superior_chat/", superior_chat, name="superior_chat"),
    path("health/", health_check, name="health_check"),  # Health check endpoint
]
