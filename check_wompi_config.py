import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from dashboard.models import WompiConfig

wompi = WompiConfig.objects.first()
if wompi:
    print(f'\n=== CONFIGURACIÓN WOMPI ACTUAL ===')
    print(f'Nombre: {wompi.nombre}')
    print(f'Environment: {wompi.environment}')
    print(f'Public Key: {wompi.public_key[:20]}...')
    print(f'Private Key: {wompi.private_key[:20]}...')
    if wompi.integrity_secret:
        print(f'Integrity Secret: ✅ {wompi.integrity_secret[:30]}...')
        print(f'\n🎉 ¡CONFIGURACIÓN COMPLETA!')
        print(f'\n✅ Wompi está listo para procesar pagos')
        print(f'   - Public Key: Configurado')
        print(f'   - Private Key: Configurado')
        print(f'   - Integrity Secret: Configurado')
        print(f'   - Environment: {wompi.environment}')
        print(f'\n💳 Ahora puedes probar pagos con tarjeta en tu checkout')
    else:
        print(f'Integrity Secret: ❌ NO CONFIGURADO')
        print(f'\n⚠️ NECESITAS AGREGAR EL INTEGRITY SECRET DESDE EL DASHBOARD')
        print(f'\nPasos:')
        print(f'1. Ve a tu Dashboard → Configuración → Wompi')
        print(f'2. Edita la configuración existente')
        print(f'3. Agrega el Integrity Secret que obtengas del panel de Wompi')
        print(f'\nDónde obtener el Integrity Secret:')
        print(f'   Panel de Wompi → Developers → API Keys → Events Key o Integrity Secret')
        print(f'   Formato: prod_integrity_xxxxxxxxxxxxxxxxxx')
else:
    print('❌ No hay configuración de Wompi')
