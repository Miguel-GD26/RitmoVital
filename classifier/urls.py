# classifier/urls.py
from django.urls import path
from .views import classify_api

urlpatterns = [
    path('api/classify/', classify_api, name='classify_api'),
    
]