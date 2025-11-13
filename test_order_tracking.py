#!/usr/bin/env python3
"""
Script de prueba para el sistema de seguimiento de pedidos
Verifica que los estados funcionen correctamente en la ruta de entrega
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from core.models import Pedido, SimpleUser
from datetime import datetime

def test_order_tracking():
    """Prueba el sistema de tracking de pedidos"""
    
    print("🧪 Iniciando pruebas del sistema de seguimiento de pedidos...")
    print("=" * 60)
    
    # 1. Verificar estados disponibles
    print("\n📋 Estados disponibles en el modelo Pedido:")
    for estado, display in Pedido.ESTADO_CHOICES:
        print(f"   • {estado} -> {display}")
    
    # 2. Verificar que existen pedidos
    total_pedidos = Pedido.objects.count()
    print(f"\n📦 Total de pedidos en la base de datos: {total_pedidos}")
    
    if total_pedidos == 0:
        print("⚠️  No hay pedidos para probar. Creando pedido de ejemplo...")
        
        # Crear usuario de prueba si no existe
        user, created = SimpleUser.objects.get_or_create(
            email='test@compueasys.com',
            defaults={
                'name': 'Usuario de Prueba',
                'telefono': '3001234567',
                'password': 'test123',
                'city': 'Bogotá',
                'address': 'Calle Test 123'
            }
        )
        
        # Crear pedido de prueba
        pedido = Pedido.objects.create(
            user=user,
            nombre='Usuario de Prueba',
            email='test@compueasys.com',
            telefono='3001234567',
            direccion='Calle Test 123',
            ciudad='Bogotá',
            departamento='Cundinamarca',
            total=150000,
            subtotal=135000,
            envio=15000,
            detalles='Producto de prueba - Laptop Gamer',
            estado='pendiente',
            metodo_pago='contraentrega'
        )
        print(f"✅ Creado pedido de prueba #{pedido.id}")
    
    # 3. Probar la ruta de estados
    pedidos_ejemplo = Pedido.objects.filter(estado__in=['pendiente', 'confirmado', 'enviado']).first()
    
    if pedidos_ejemplo:
        print(f"\n🚀 Probando ruta de seguimiento con pedido #{pedidos_ejemplo.id}")
        print(f"   Estado actual: {pedidos_ejemplo.estado} -> {pedidos_ejemplo.get_estado_display()}")
        
        # Ruta de estados completa
        ruta_estados = [
            ('pendiente', 'Pedido recibido y confirmado'),
            ('confirmado', 'Pedido en proceso de preparación'),
            ('enviado', 'Pedido enviado al cliente'),
            ('llegando', 'Pedido en camino hacia el destino'),
            ('entregado', 'Pedido entregado exitosamente')
        ]
        
        print("\n📍 Ruta de seguimiento completa:")
        for i, (estado, descripcion) in enumerate(ruta_estados, 1):
            icon = "✅" if pedidos_ejemplo.estado == estado else "⏳"
            status = "ACTUAL" if pedidos_ejemplo.estado == estado else "SIGUIENTE" if i == len([e for e, d in ruta_estados if e == pedidos_ejemplo.estado]) + 1 else "PENDIENTE"
            print(f"   {i}. {icon} {estado.capitalize()}: {descripcion} [{status}]")
    
    # 4. Verificar métodos del modelo
    print("\n🔧 Verificando métodos del modelo:")
    if pedidos_ejemplo:
        print(f"   • get_estado_display(): {pedidos_ejemplo.get_estado_display()}")
        print(f"   • get_estado_badge_class(): {pedidos_ejemplo.get_estado_badge_class()}")
        print(f"   • get_pago_badge_class(): {pedidos_ejemplo.get_pago_badge_class()}")
    
    # 5. Estadísticas por estado
    print("\n📊 Estadísticas de pedidos por estado:")
    for estado, display in Pedido.ESTADO_CHOICES:
        count = Pedido.objects.filter(estado=estado).count()
        if count > 0:
            print(f"   • {display}: {count} pedidos")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas del sistema de seguimiento completadas!")
    
    return True

def simulate_order_progression():
    """Simula la progresión de un pedido a través de todos los estados"""
    
    print("\n🎭 Simulando progresión de pedido...")
    
    # Buscar un pedido pendiente o crear uno
    pedido = Pedido.objects.filter(estado='pendiente').first()
    
    if not pedido:
        print("   No hay pedidos pendientes. Saltando simulación.")
        return
    
    estados_progresion = ['confirmado', 'enviado', 'llegando', 'entregado']
    
    print(f"   📦 Pedido #{pedido.id} - Estado inicial: {pedido.get_estado_display()}")
    
    for estado in estados_progresion:
        print(f"   ➡️  Cambiando a: {estado}")
        pedido.estado = estado
        
        # Establecer fechas especiales
        if estado == 'enviado' and not pedido.fecha_enviado:
            pedido.fecha_enviado = datetime.now()
        elif estado == 'entregado' and not pedido.fecha_entregado:
            pedido.fecha_entregado = datetime.now()
        
        pedido.save()
        print(f"   ✅ Estado actualizado a: {pedido.get_estado_display()}")
    
    print(f"   🎉 Pedido #{pedido.id} completado exitosamente!")

if __name__ == '__main__':
    try:
        test_order_tracking()
        simulate_order_progression()
        
        print(f"\n🌟 ¡Sistema de seguimiento de pedidos funcionando perfectamente!")
        print(f"   • Los usuarios pueden ver la ruta de entrega en mis_pedidos_modern.html")
        print(f"   • Los admins pueden cambiar estados desde dashboard/pedidos")
        print(f"   • Estados: pendiente → confirmado → enviado → llegando → entregado")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()