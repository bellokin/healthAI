# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.suggest_career_path, name='suggestCareerPpath'),  # Define a path for the home view
]
