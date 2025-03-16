"""
URL configuration for superior_chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse

# Health check endpoint
def health_check(request):
    return JsonResponse({"status": "ok"})

# Default API Root View
def api_root(request):
    return JsonResponse({"message": "Welcome to the Superior Chatbot API!"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("chatbot.urls")),  # Ensure chatbot URLs are included
    path("health/", health_check, name="health_check"),  # Health check endpoint
    path("", api_root),  # Add this to return a response on the base URL
]

# Enable admin only in development
if os.getenv("ENVIRONMENT") == "development":
    urlpatterns.append(path("admin/", admin.site.urls))
