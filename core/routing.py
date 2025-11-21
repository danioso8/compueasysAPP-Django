from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/store/$', consumers.StoreVisitConsumer.as_asgi()),
    re_path(r'ws/dashboard/$', consumers.DashboardAdminConsumer.as_asgi()),
]
