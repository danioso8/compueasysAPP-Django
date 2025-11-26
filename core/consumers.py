import json
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime


from channels.db import database_sync_to_async

class StoreVisitConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Guardar la visita en la base de datos
        await self.save_visit()
        # Notificar conexión al grupo de admins
        await self.channel_layer.group_send(
            'dashboard_admins',
            {
                'type': 'dashboard.notify',
                'message': 'new_visit',
                'timestamp': datetime.now().isoformat()
            }
        )
        await self.send(json.dumps({
            'message': 'visit_registered',
            'timestamp': datetime.now().isoformat()
        }))

    @database_sync_to_async
    def save_visit(self):
        # Importar modelos aquí para evitar AppRegistryNotReady
        from .models import StoreVisit, SimpleUser
        user = None
        try:
            user_id = self.scope.get('user').id if self.scope.get('user') and self.scope.get('user').is_authenticated else None
            if user_id:
                user = SimpleUser.objects.filter(id=user_id).first()
        except Exception:
            user = None
        session_key = self.scope.get('session').session_key if self.scope.get('session') else None
        StoreVisit.objects.create(session_key=session_key, user=user, visit_type='store')

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        pass

# Consumer para admins del dashboard
class DashboardAdminConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('dashboard_admins', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('dashboard_admins', self.channel_name)

    async def dashboard_notify(self, event):
        await self.send(json.dumps({
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
