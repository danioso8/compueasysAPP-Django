# relay_views.py - Servidor Relay para Remote Support
import json
import asyncio
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from collections import defaultdict
import time

# Almacenamiento en memoria para conexiones activas
active_sessions = {}  # session_id -> {'client': data, 'technician': data, 'messages': []}
pending_messages = defaultdict(list)  # session_id -> [messages]


@require_http_methods(["GET"])
def relay_status(request):
    """Endpoint de status del relay server"""
    return JsonResponse({
        'success': True,
        'status': 'online',
        'active_sessions': len(active_sessions),
        'message': 'CompuEasys Remote Support Relay Server'
    })


@csrf_exempt
@require_http_methods(["POST"])
def register_client(request):
    """Cliente registra su sesión automáticamente"""
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        client_name = data.get('client_name', 'Cliente')
        os_info = data.get('os', 'Unknown')
        
        # Crear nueva sesión
        session_id = f"session_{client_id}_{int(time.time())}"
        active_sessions[session_id] = {
            'client_id': client_id,
            'client_name': client_name,
            'os': os_info,
            'client_connected': True,
            'technician_connected': False,
            'authorization_pending': False,
            'authorized': False,
            'created_at': time.time()
        }
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'message': 'Cliente registrado exitosamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def connect_technician(request):
    """Técnico se conecta a sesión con código de acceso"""
    try:
        data = json.loads(request.body)
        access_code = data.get('access_code')
        
        # Buscar sesión con este código
        session_id = None
        for sid, session in active_sessions.items():
            if session['access_code'] == access_code and session['client_connected']:
                session_id = sid
                session['technician_connected'] = True
                break
        
        if session_id:
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'message': 'Técnico conectado exitosamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Código de acceso inválido o sesión no encontrada'
            }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Enviar mensaje a través del relay (cliente -> técnico o viceversa)"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message = data.get('message')
        sender = data.get('sender')  # 'client' o 'technician'
        
        if session_id not in active_sessions:
            return JsonResponse({'success': False, 'error': 'Sesión no encontrada'}, status=404)
        
        # Guardar mensaje para el receptor
        pending_messages[session_id].append({
            'sender': sender,
            'message': message,
            'timestamp': time.time()
        })
        
        return JsonResponse({'success': True, 'message': 'Mensaje enviado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def receive_messages(request):
    """Recibir mensajes pendientes (long polling)"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        receiver = data.get('receiver')  # 'client' o 'technician'
        
        if session_id not in active_sessions:
            return JsonResponse({'success': False, 'error': 'Sesión no encontrada'}, status=404)
        
        # Obtener mensajes pendientes para este receptor
        messages = []
        if session_id in pending_messages:
            for msg in pending_messages[session_id]:
                # Solo enviar mensajes del otro extremo
                if msg['sender'] != receiver:
                    messages.append(msg)
            
            # Limpiar mensajes enviados
            pending_messages[session_id] = [
                msg for msg in pending_messages[session_id] 
                if msg['sender'] == receiver
            ]
        
        return JsonResponse({
            'success': True,
            'messages': messages,
            'session_active': active_sessions[session_id]['client_connected'] and 
                            active_sessions[session_id]['technician_connected']
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def disconnect(request):
    """Desconectar cliente o técnico"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        who = data.get('who')  # 'client' o 'technician'
        
        if session_id in active_sessions:
            if who == 'client':
                active_sessions[session_id]['client_connected'] = False
            else:
                active_sessions[session_id]['technician_connected'] = False
            
            # Si ambos desconectaron, eliminar sesión
            if not (active_sessions[session_id]['client_connected'] or 
                   active_sessions[session_id]['technician_connected']):
                del active_sessions[session_id]
                if session_id in pending_messages:
                    del pending_messages[session_id]
        
        return JsonResponse({'success': True, 'message': 'Desconectado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def list_active_sessions(request):
    """Listar sesiones activas (solo para clientes esperando)"""
    try:
        sessions = []
        for session_id, session in active_sessions.items():
            if session['client_connected'] and not session['technician_connected']:
                sessions.append({
                    'session_id': session_id,
                    'client_id': session['client_id'],
                    'client_name': session.get('client_name', 'Cliente'),
                    'os': session.get('os', 'Unknown'),
                    'created_at': session['created_at']
                })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def request_connection(request):
    """Técnico solicita conectarse a un cliente (sin código)"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        technician_name = data.get('technician_name', 'Técnico CompuEasys')
        
        if session_id in active_sessions:
            session = active_sessions[session_id]
            session['authorization_pending'] = True
            session['technician_name'] = technician_name
            session['connection_request_time'] = time.time()
            
            return JsonResponse({
                'success': True,
                'message': 'Solicitud enviada al cliente'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Sesión no encontrada'
            }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def check_connection_request(request):
    """Cliente verifica si hay solicitud de conexión (long polling)"""
    try:
        session_id = request.GET.get('session_id')
        
        if session_id in active_sessions:
            session = active_sessions[session_id]
            
            # Long polling: esperar hasta 25s por una solicitud
            max_wait = 25
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if session.get('authorization_pending'):
                    return JsonResponse({
                        'success': True,
                        'connection_request': True,
                        'technician_name': session.get('technician_name', 'Técnico')
                    })
                time.sleep(1)
            
            # Timeout sin solicitud
            return JsonResponse({
                'success': True,
                'connection_request': False
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Sesión no encontrada'
            }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def authorize_connection(request):
    """Cliente autoriza o deniega la conexión"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        authorized = data.get('authorized', False)
        
        if session_id in active_sessions:
            session = active_sessions[session_id]
            session['authorization_pending'] = False
            session['authorized'] = authorized
            session['authorization_time'] = time.time()
            
            if authorized:
                session['technician_connected'] = True
            
            return JsonResponse({
                'success': True,
                'authorized': authorized
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Sesión no encontrada'
            }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def check_authorization(request):
    """Técnico verifica si el cliente autorizó la conexión"""
    try:
        session_id = request.GET.get('session_id')
        
        if session_id in active_sessions:
            session = active_sessions[session_id]
            
            # Long polling: esperar hasta 30s por autorización
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if not session.get('authorization_pending', False):
                    # Ya hubo respuesta
                    return JsonResponse({
                        'success': True,
                        'authorized': session.get('authorized', False),
                        'responded': True
                    })
                time.sleep(1)
            
            # Timeout
            return JsonResponse({
                'success': True,
                'authorized': False,
                'responded': False,
                'timeout': True
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Sesión no encontrada'
            }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# Limpieza automática de sesiones antiguas (> 24 horas)
def cleanup_old_sessions():
    """Función para limpiar sesiones viejas (llamar periódicamente)"""
    current_time = time.time()
    old_sessions = []
    
    for session_id, session in active_sessions.items():
        # 24 horas = 86400 segundos
        if current_time - session['created_at'] > 86400:
            old_sessions.append(session_id)
    
    for session_id in old_sessions:
        del active_sessions[session_id]
        if session_id in pending_messages:
            del pending_messages[session_id]
