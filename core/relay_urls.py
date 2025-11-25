# relay_urls.py - URLs para el servidor relay
from django.urls import path
from . import relay_views

urlpatterns = [
    path('', relay_views.relay_status, name='relay_status'),  # Endpoint base
    path('register_client/', relay_views.register_client, name='relay_register_client'),
    path('connect_technician/', relay_views.connect_technician, name='relay_connect_technician'),
    path('send_message/', relay_views.send_message, name='relay_send_message'),
    path('receive_messages/', relay_views.receive_messages, name='relay_receive_messages'),
    path('disconnect/', relay_views.disconnect, name='relay_disconnect'),
    path('list_sessions/', relay_views.list_active_sessions, name='relay_list_sessions'),
]
