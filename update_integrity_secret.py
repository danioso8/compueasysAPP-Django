import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from dashboard.models import WompiConfig

def update_integrity_secret():
    wompi = WompiConfig.objects.first()
    
    if not wompi:
        print('❌ No hay configuración de Wompi. Créala primero desde el dashboard.')
        return
    
    print('\n=== CONFIGURACIÓN WOMPI ACTUAL ===')
    print(f'Nombre: {wompi.nombre}')
    print(f'Environment: {wompi.environment}')
    print(f'Public Key: {wompi.public_key[:20]}...')
    print(f'Private Key: {wompi.private_key[:20]}...')
    print(f'Base URL: {wompi.base_url}')
    print(f'Integrity Secret: {wompi.integrity_secret if wompi.integrity_secret else "❌ NO CONFIGURADO"}\n')
    
    # Solicitar el integrity secret
    print('📝 Ingresa el Integrity Secret de Wompi')
    print('   (Encuéntralo en: Panel de Wompi → Developers → API Keys → Events Key)')
    print('   Formato: prod_integrity_xxxxxxxxxxxxxxxxxx\n')
    
    integrity_secret = input('Integrity Secret: ').strip()
    
    if not integrity_secret:
        print('❌ No se ingresó ningún valor. Operación cancelada.')
        return
    
    # Validar formato básico
    if not integrity_secret.startswith('prod_integrity_') and not integrity_secret.startswith('test_integrity_'):
        print('⚠️ ADVERTENCIA: El formato no parece correcto.')
        print('   Debería empezar con "prod_integrity_" o "test_integrity_"')
        confirmar = input('¿Continuar de todos modos? (s/n): ').strip().lower()
        if confirmar != 's':
            print('❌ Operación cancelada.')
            return
    
    # Guardar
    wompi.integrity_secret = integrity_secret
    wompi.save()
    
    print('\n✅ Integrity Secret actualizado exitosamente')
    print(f'\n=== NUEVA CONFIGURACIÓN ===')
    print(f'Nombre: {wompi.nombre}')
    print(f'Environment: {wompi.environment}')
    print(f'Integrity Secret: {wompi.integrity_secret[:25]}...')
    print('\n🎉 ¡Listo! Ahora puedes probar los pagos con Wompi.')
    print('   Los pagos deberían funcionar correctamente.')

if __name__ == '__main__':
    try:
        update_integrity_secret()
    except KeyboardInterrupt:
        print('\n\n❌ Operación cancelada por el usuario.')
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
