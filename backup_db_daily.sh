#!/bin/bash
# ================================================================
# BACKUP AUTOMÁTICO DIARIO DE POSTGRESQL - CompuEasysApp
# ================================================================

# Configuración
DB_NAME="compueasys_db"
DB_USER="compueasys_user"
DB_PASSWORD="CompuEasys2026!"
BACKUP_DIR="/var/backups/compueasys"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"
LOG_FILE="$BACKUP_DIR/backup.log"
RETENTION_DAYS=7

# Crear directorio de backups si no existe
mkdir -p $BACKUP_DIR

# Función para logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

log_message "====== INICIANDO BACKUP DIARIO ======"

# Realizar backup con pg_dump
export PGPASSWORD=$DB_PASSWORD
if pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE; then
    # Comprimir el backup
    gzip $BACKUP_FILE
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # Calcular tamaño
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    
    log_message "✅ Backup completado exitosamente"
    log_message "   Archivo: $(basename $BACKUP_FILE)"
    log_message "   Tamaño: $SIZE"
    
    # Eliminar backups antiguos (mantener solo últimos RETENTION_DAYS días)
    find $BACKUP_DIR -name "backup_${DB_NAME}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    DELETED=$(find $BACKUP_DIR -name "backup_${DB_NAME}_*.sql.gz" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
    
    if [ $DELETED -gt 0 ]; then
        log_message "🗑️  Eliminados $DELETED backups antiguos (>$RETENTION_DAYS días)"
    fi
    
    # Contar backups actuales
    TOTAL_BACKUPS=$(ls -1 $BACKUP_DIR/backup_${DB_NAME}_*.sql.gz 2>/dev/null | wc -l)
    log_message "📊 Total de backups almacenados: $TOTAL_BACKUPS"
    
else
    log_message "❌ ERROR: Falló el backup de la base de datos"
    exit 1
fi

unset PGPASSWORD

log_message "====== BACKUP FINALIZADO ======"
echo ""

# Mostrar últimos 5 backups
echo "Últimos backups disponibles:"
ls -lht $BACKUP_DIR/backup_${DB_NAME}_*.sql.gz 2>/dev/null | head -5

exit 0
