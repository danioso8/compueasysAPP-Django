#!/bin/bash

# Script para verificar DNS e instalar SSL automáticamente
DOMAIN="compueasys.com"
WWW_DOMAIN="www.compueasys.com"
TARGET_IP="84.247.129.180"
EMAIL="danioso8@hotmail.com"

echo "======================================"
echo "Verificador DNS y SSL Automático"
echo "======================================"
echo ""

# Función para verificar DNS
check_dns() {
    echo "🔍 Verificando DNS de $1..."
    IPS=$(dig +short $1 | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')
    
    if echo "$IPS" | grep -q "$TARGET_IP"; then
        # Verificar que NO tenga otras IPs
        IP_COUNT=$(echo "$IPS" | wc -l)
        if [ "$IP_COUNT" -eq 1 ]; then
            echo "✅ $1 apunta correctamente a $TARGET_IP"
            return 0
        else
            echo "⚠️  $1 tiene múltiples IPs:"
            echo "$IPS"
            echo "   Esperando que solo quede $TARGET_IP..."
            return 1
        fi
    else
        echo "❌ $1 NO apunta a $TARGET_IP"
        echo "   IPs actuales:"
        echo "$IPS"
        return 1
    fi
}

# Loop de verificación
echo "Esperando propagación DNS..."
echo "(Esto puede tomar 5-30 minutos)"
echo ""

MAX_ATTEMPTS=60  # 30 minutos máximo (checks cada 30 segundos)
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Intento $ATTEMPT de $MAX_ATTEMPTS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Verificar ambos dominios
    if check_dns "$DOMAIN" && check_dns "$WWW_DOMAIN"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ DNS PROPAGADO CORRECTAMENTE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Instalar SSL
        echo "🔒 Instalando certificado SSL..."
        echo ""
        
        certbot --nginx \
            -d $DOMAIN \
            -d $WWW_DOMAIN \
            --non-interactive \
            --agree-tos \
            --email $EMAIL \
            --redirect
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "✅ SSL INSTALADO EXITOSAMENTE"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "🌐 Tu sitio está disponible en:"
            echo "   https://compueasys.com"
            echo "   https://www.compueasys.com"
            echo ""
            echo "🔒 Características:"
            echo "   ✅ Certificado SSL/TLS activo"
            echo "   ✅ HTTP redirige automáticamente a HTTPS"
            echo "   ✅ Renovación automática configurada"
            echo ""
            echo "📊 Información del certificado:"
            certbot certificates -d $DOMAIN
            echo ""
            
            # Actualizar configuración de seguridad en Django
            echo "🐍 Actualizando configuración de seguridad Django..."
            cd /var/www/CompuEasysApp
            
            # Actualizar .env para habilitar HTTPS
            sed -i 's/SESSION_COOKIE_SECURE = False/SESSION_COOKIE_SECURE = True/' AppCompueasys/settings.py
            sed -i 's/CSRF_COOKIE_SECURE = False/CSRF_COOKIE_SECURE = True/' AppCompueasys/settings.py
            
            # Reiniciar servicios
            echo "🔄 Reiniciando servicios..."
            systemctl restart compueasys
            systemctl reload nginx
            
            echo ""
            echo "✅ ¡Configuración completada!"
            echo "   Visita https://compueasys.com para verificar"
            echo ""
            
            exit 0
        else
            echo ""
            echo "❌ Error al instalar SSL"
            echo "   Revisa los logs: /var/log/letsencrypt/letsencrypt.log"
            echo ""
            exit 1
        fi
    else
        echo ""
        echo "⏳ DNS aún no propagado completamente"
        echo "   Esperando 30 segundos para el próximo intento..."
        echo ""
        sleep 30
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏰ TIMEOUT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "El DNS no se ha propagado después de 30 minutos."
echo "Esto puede deberse a:"
echo "  1. Los cambios DNS aún no se han aplicado en Hostinger"
echo "  2. La propagación DNS global toma más tiempo"
echo "  3. Hay un problema con la configuración DNS"
echo ""
echo "Puedes:"
echo "  1. Ejecutar este script nuevamente más tarde"
echo "  2. Verificar manualmente: dig compueasys.com +short"
echo "  3. Usar https://dnschecker.org/#A/compueasys.com"
echo ""
exit 1
