#!/bin/bash
# ================================================================
# SCRIPT PARA RESTAURAR BACKUP DE POSTGRESQL - CompuEasysApp
# ================================================================
# Uso: ./restore_backup.sh [archivo_backup.sql.gz]

DB_NAME="compueasys_db"
DB_USER="compueasys_user"
DB_PASSWORD="CompuEasys2026!"
BACKUP_DIR="/var/backups/compueasys"

echo "================================================================"
echo "  RESTAURAR BACKUP - CompuEasysApp PostgreSQL"
echo "================================================================"
echo ""

# Si no se proporciona archivo, mostrar backups disponibles
if [ -z "$1" ]; then
    echo "Backups disponibles:"
    echo ""
    ls -lht $BACKUP_DIR/backup_*.sql.gz 2>/dev/null | nl
    echo ""
    echo "Uso: $0 <archivo_backup.sql.gz>"
    echo "Ejemplo: $0 /var/backups/compueasys/backup_compueasys_db_20260115_192156.sql.gz"
    exit 1
fi

BACKUP_FILE=$1

# Verificar que el archivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ ERROR: El archivo $BACKUP_FILE no existe"
    exit 1
fi

echo "⚠️  ADVERTENCIA: Esta operación ELIMINARÁ todos los datos actuales"
echo "   y los reemplazará con el backup: $(basename $BACKUP_FILE)"
echo ""
read -p "¿Estás seguro? (escribe 'SI' para continuar): " confirmacion

if [ "$confirmacion" != "SI" ]; then
    echo "❌ Operación cancelada"
    exit 0
fi

echo ""
echo "🔄 Descomprimiendo backup..."
TEMP_FILE="/tmp/restore_temp.sql"
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

echo "🗑️  Eliminando base de datos actual..."
export PGPASSWORD=$DB_PASSWORD
dropdb -U $DB_USER -h localhost --if-exists $DB_NAME

echo "📦 Creando nueva base de datos..."
createdb -U $DB_USER -h localhost $DB_NAME

echo "⬆️  Restaurando backup..."
if psql -U $DB_USER -h localhost $DB_NAME < "$TEMP_FILE"; then
    echo ""
    echo "✅ Backup restaurado exitosamente"
    echo "   Base de datos: $DB_NAME"
    echo "   Desde archivo: $(basename $BACKUP_FILE)"
else
    echo ""
    echo "❌ ERROR: Falló la restauración del backup"
    rm -f "$TEMP_FILE"
    exit 1
fi

# Limpiar archivo temporal
rm -f "$TEMP_FILE"
unset PGPASSWORD

echo ""
echo "🔄 Reiniciando servicio..."
systemctl restart compueasys

echo ""
echo "================================================================"
echo "  ✅ RESTAURACIÓN COMPLETADA"
echo "================================================================"

exit 0
