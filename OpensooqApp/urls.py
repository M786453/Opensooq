from django.urls import path
from . import views

urlpatterns = [
    path('opensooq', views.opensooq, name='opensooq'),
]