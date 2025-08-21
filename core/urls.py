from django.urls import path
from .views import worker_request

urlpatterns = [
    path("api/", worker_request, name="worker_request"),
]
