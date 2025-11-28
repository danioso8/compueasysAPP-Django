# 🚨 PROBLEMA IDENTIFICADO - Pagos con Tarjeta Wompi

## ❌ PROBLEMA PRINCIPAL

Estás intentando hacer pruebas de pago con **credenciales de PRODUCCIÓN** (`pub_prod_xxx`).

### ¿Por qué no funciona?
1. Las credenciales de PRODUCCIÓN están configuradas para pagos REALES
2. Las tarjetas de prueba (4242 4242 4242 4242) NO funcionan en producción
3. Solo funcionan con tarjetas reales, y se cobrarán los montos

## ✅ SOLUCIÓN

### Opción 1: Usar Credenciales de TEST (Recomendado)

1. **Obtener credenciales de TEST de Wompi:**
   - Ir a https://wompi.co
   - Iniciar sesión en tu cuenta
   - Ir a **Configuración → API Keys**
   - Copiar las claves de **SANDBOX/TEST**:
     - `pub_test_xxxxxxxxxxxxxxxxxx` (Public Key TEST)
     - `prv_test_xxxxxxxxxxxxxxxxxx` (Private Key TEST)

2. **Actualizar en el Dashboard:**
   ```
   1. Ir al Dashboard de CompuEasys
   2. Configuración → Wompi
   3. Cambiar credenciales a las de TEST
   4. Guardar
   ```

3. **Usar tarjetas de prueba:**
   ```
   Tarjeta APROBADA:
   Número: 4242 4242 4242 4242
   CVV: 123
   Fecha: 12/25
   Nombre: APPROVED
   ```

### Opción 2: Probar con Tarjeta Real (NO Recomendado)

Si mantienes las credenciales de PRODUCCIÓN:
- ⚠️  **Usarás tu tarjeta real**
- ⚠️  **Se cobrará el monto real**
- ⚠️  **No es una prueba, es una compra real**

Solo usa esta opción si:
- Ya terminaste las pruebas
- Estás seguro de que todo funciona
- Quieres hacer una compra real

## 📝 PASOS PARA RESOLVER

### Paso 1: Obtener Credenciales de TEST

Ve a https://wompi.co y copia tus credenciales de SANDBOX/TEST

### Paso 2: Actualizar en Dashboard

```bash
# Ejecutar el script helper:
python switch_wompi_to_test.py

# Luego actualizar las credenciales manualmente en el Dashboard
```

### Paso 3: Ejecutar Diagnóstico

```bash
python test_wompi_payment_flow.py
```

Deberías ver:
- ✅ Config
- ✅ Client
- ✅ Acceptance Token
- ✅ Transaction
- ✅ Endpoint
- ✅ Env Vars

### Paso 4: Probar Pago

1. Ir al checkout
2. Seleccionar "Recoger en Tienda + Tarjeta"
3. Usar tarjeta de prueba:
   ```
   4242 4242 4242 4242
   CVV: 123
   Fecha: 12/25
   Nombre: APPROVED
   ```
4. El pago debería ser aprobado ✅

## 🔍 ¿Por qué es importante usar TEST?

### Modo TEST (Sandbox):
- ✅ No se cobran montos reales
- ✅ Puedes probar múltiples veces
- ✅ Tarjetas de prueba funcionan
- ✅ Puedes simular aprobaciones, rechazos, errores
- ✅ No afecta tu cuenta bancaria

### Modo PRODUCCIÓN:
- ⚠️  Cobros reales a tarjetas reales
- ⚠️  Tarjetas de prueba NO funcionan
- ⚠️  Cada prueba es un cobro real
- ⚠️  Afecta tus finanzas

## 💡 Información Adicional

### ¿Dónde están las credenciales de TEST en Wompi?

1. Inicia sesión en https://wompi.co
2. En el menú lateral: **Desarrolladores** o **API Keys**
3. Verás dos tabs:
   - **Sandbox/Test** ← Usar estas
   - **Producción** ← NO usar para pruebas
4. Copia:
   - Public Key (pub_test_xxx)
   - Private Key (prv_test_xxx)

### ¿Cómo actualizar en el Dashboard?

```
1. Ir a: http://localhost:8000/dashboard/
2. Click en "Configuración" (menú lateral)
3. Click en "Wompi"
4. Actualizar:
   - Public Key: pub_test_xxx
   - Private Key: prv_test_xxx
   - Environment: test
   - Base URL: https://sandbox.wompi.co/v1
5. Guardar cambios
```

## 🎯 Checklist de Verificación

Antes de volver a probar, verifica:

- [ ] Credenciales de TEST obtenidas de Wompi
- [ ] Dashboard actualizado con credenciales TEST
- [ ] Environment = "test"
- [ ] Base URL = "https://sandbox.wompi.co/v1"
- [ ] Script de diagnóstico ejecutado exitosamente
- [ ] Todas las pruebas en verde ✅

## 🆘 Si Sigues con Problemas

1. **Ejecutar diagnóstico completo:**
   ```bash
   python test_wompi_payment_flow.py
   ```

2. **Capturar logs:**
   - Consola del navegador (F12 → Console)
   - Logs del servidor Django
   - Copiar todos los mensajes de error

3. **Verificar credenciales:**
   - ¿Son de TEST o de PRODUCCIÓN?
   - ¿Están completas (sin espacios extra)?
   - ¿Son válidas en Wompi?

4. **Revisar documento:**
   ```
   DIAGNOSTICO_WOMPI_PAGOS.md
   ```

## 📞 Soporte Wompi

Si necesitas ayuda con las credenciales:
- Email: soporte@wompi.com
- Documentación: https://docs.wompi.co
- Chat en vivo: https://wompi.co (esquina inferior derecha)

---

**⚡ RESUMEN RÁPIDO:**
Necesitas cambiar tus credenciales de PRODUCCIÓN (`pub_prod_xxx`) a credenciales de TEST (`pub_test_xxx`) para poder probar pagos sin cobros reales. Obtén las credenciales de TEST desde tu cuenta de Wompi → API Keys → Sandbox.
