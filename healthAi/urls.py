# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_assistant, name='health_assistant'),  # Define a path for the home view
]
