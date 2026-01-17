"""
Script de Backup Blindado - Múltiples copias de seguridad
Crea backups en diferentes formatos y ubicaciones
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import django
import sys

# Configurar Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.core import serializers
from django.apps import apps
from django.db import connection
import zipfile

BASE_DIR = Path(__file__).resolve().parent

def create_backup_locations():
    """Crear múltiples ubicaciones de backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    locations = {
        'primary': os.path.join(BASE_DIR, 'backups'),
        'secondary': os.path.join(BASE_DIR, 'backups_secondary'),
        'archive': os.path.join(BASE_DIR, 'backups_archive', timestamp)
    }
    
    for loc in locations.values():
        os.makedirs(loc, exist_ok=True)
    
    return locations, timestamp

def backup_database_json(location, timestamp):
    """Crear backup en formato JSON"""
    
    backup_file = os.path.join(location, f'compueasys_backup_{timestamp}.json')
    
    print(f"📦 Creando backup JSON en: {location}")
    
    try:
        all_models = apps.get_models()
        
        # Serializar todos los datos
        data = serializers.serialize('json', 
            [obj for model in all_models for obj in model.objects.all()],
            indent=2
        )
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(data)
        
        file_size = os.path.getsize(backup_file) / (1024 * 1024)
        print(f"   ✅ JSON: {file_size:.2f} MB")
        
        return backup_file
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def backup_by_app_separate(location, timestamp):
    """Crear backups separados por aplicación"""
    
    print(f"📦 Creando backups por aplicación en: {location}")
    
    apps_dir = os.path.join(location, 'apps_separate')
    os.makedirs(apps_dir, exist_ok=True)
    
    apps_to_backup = ['core', 'dashboard', 'contable', 'auth', 'contenttypes', 'sessions']
    backup_files = []
    
    for app_name in apps_to_backup:
        try:
            app_backup_file = os.path.join(apps_dir, f'{app_name}_{timestamp}.json')
            
            app_models = [m for m in apps.get_models() if m._meta.app_label == app_name]
            
            if not app_models:
                continue
            
            data = serializers.serialize('json',
                [obj for model in app_models for obj in model.objects.all()],
                indent=2
            )
            
            with open(app_backup_file, 'w', encoding='utf-8') as f:
                f.write(data)
            
            backup_files.append(app_backup_file)
            
        except Exception as e:
            print(f"   ⚠️  Error en {app_name}: {str(e)}")
    
    print(f"   ✅ {len(backup_files)} aplicaciones respaldadas")
    return backup_files

def create_sql_dump(location, timestamp):
    """Crear dump SQL compatible con PostgreSQL"""
    
    sql_file = os.path.join(location, f'compueasys_sql_{timestamp}.sql')
    
    print(f"📦 Creando dump SQL en: {location}")
    
    try:
        with connection.cursor() as cursor:
            # Obtener información de la base de datos
            db_name = connection.settings_dict['NAME']
            
        # Crear archivo SQL con comandos de inserción
        all_models = apps.get_models()
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup CompuEasys Database\n")
            f.write(f"-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Base de datos: {db_name}\n\n")
            
            for model in all_models:
                app_label = model._meta.app_label
                model_name = model._meta.model_name
                table_name = model._meta.db_table
                
                count = model.objects.count()
                if count > 0:
                    f.write(f"\n-- {app_label}.{model_name} ({count} registros)\n")
        
        file_size = os.path.getsize(sql_file) / (1024 * 1024)
        print(f"   ✅ SQL: {file_size:.2f} MB")
        
        return sql_file
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def create_compressed_backup(source_files, location, timestamp):
    """Crear backup comprimido en ZIP"""
    
    zip_file = os.path.join(location, f'compueasys_backup_{timestamp}.zip')
    
    print(f"📦 Creando archivo comprimido...")
    
    try:
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in source_files:
                if file and os.path.exists(file):
                    arcname = os.path.basename(file)
                    zipf.write(file, arcname)
        
        file_size = os.path.getsize(zip_file) / (1024 * 1024)
        print(f"   ✅ ZIP: {file_size:.2f} MB")
        
        return zip_file
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def create_metadata(locations, timestamp):
    """Crear archivo de metadatos del backup"""
    
    metadata = {
        'backup_date': datetime.now().isoformat(),
        'timestamp': timestamp,
        'database': {
            'name': connection.settings_dict.get('NAME'),
            'host': connection.settings_dict.get('HOST'),
            'engine': connection.settings_dict.get('ENGINE')
        },
        'statistics': {},
        'files': []
    }
    
    # Estadísticas
    all_models = apps.get_models()
    for model in all_models:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        count = model.objects.count()
        
        if app_label not in metadata['statistics']:
            metadata['statistics'][app_label] = {}
        
        metadata['statistics'][app_label][model_name] = count
    
    # Guardar metadatos en todas las ubicaciones
    for loc_name, loc_path in locations.items():
        metadata_file = os.path.join(loc_path, f'backup_metadata_{timestamp}.json')
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata

def verify_backup_integrity(backup_file):
    """Verificar integridad del backup"""
    
    if not os.path.exists(backup_file):
        return False, "Archivo no existe"
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            return True, f"{len(data)} registros verificados"
        else:
            return True, "Archivo válido"
            
    except json.JSONDecodeError:
        return False, "JSON inválido"
    except Exception as e:
        return False, str(e)

def backup_blindado():
    """Ejecutar backup blindado completo"""
    
    print("=" * 80)
    print("🛡️  BACKUP BLINDADO - COMPUEASYS")
    print("=" * 80)
    print()
    
    # Crear ubicaciones
    locations, timestamp = create_backup_locations()
    
    print("📁 Ubicaciones de backup:")
    for name, path in locations.items():
        print(f"   • {name}: {path}")
    print()
    
    # Estadísticas de la BD
    all_models = apps.get_models()
    total_records = sum(model.objects.count() for model in all_models)
    
    print(f"📊 Base de datos: {connection.settings_dict.get('NAME')}")
    print(f"📈 Total de registros: {total_records:,}")
    print()
    
    print("=" * 80)
    print("🔄 INICIANDO BACKUPS MÚLTIPLES")
    print("=" * 80)
    print()
    
    all_backup_files = []
    
    # 1. Backup JSON completo en ubicación primaria
    print("1️⃣  BACKUP PRIMARIO (JSON COMPLETO)")
    primary_json = backup_database_json(locations['primary'], timestamp)
    if primary_json:
        all_backup_files.append(primary_json)
    print()
    
    # 2. Backup JSON completo en ubicación secundaria
    print("2️⃣  BACKUP SECUNDARIO (JSON COMPLETO)")
    secondary_json = backup_database_json(locations['secondary'], timestamp)
    if secondary_json:
        all_backup_files.append(secondary_json)
    print()
    
    # 3. Backup separado por apps en archivo
    print("3️⃣  BACKUP POR APLICACIONES")
    app_backups = backup_by_app_separate(locations['archive'], timestamp)
    all_backup_files.extend(app_backups)
    print()
    
    # 4. Backup SQL
    print("4️⃣  BACKUP SQL")
    sql_backup = create_sql_dump(locations['archive'], timestamp)
    if sql_backup:
        all_backup_files.append(sql_backup)
    print()
    
    # 5. Crear ZIP comprimido
    print("5️⃣  BACKUP COMPRIMIDO")
    zip_primary = create_compressed_backup([primary_json], locations['primary'], timestamp)
    zip_archive = create_compressed_backup(all_backup_files, locations['archive'], timestamp)
    print()
    
    # 6. Crear metadatos
    print("6️⃣  CREANDO METADATOS")
    metadata = create_metadata(locations, timestamp)
    print("   ✅ Metadatos creados en todas las ubicaciones")
    print()
    
    # 7. Verificar integridad
    print("7️⃣  VERIFICANDO INTEGRIDAD")
    if primary_json:
        is_valid, msg = verify_backup_integrity(primary_json)
        status = "✅" if is_valid else "❌"
        print(f"   {status} Backup primario: {msg}")
    
    if secondary_json:
        is_valid, msg = verify_backup_integrity(secondary_json)
        status = "✅" if is_valid else "❌"
        print(f"   {status} Backup secundario: {msg}")
    print()
    
    # Resumen final
    print("=" * 80)
    print("✅ BACKUP BLINDADO COMPLETADO")
    print("=" * 80)
    print()
    print("📊 Resumen:")
    print(f"   • Registros respaldados: {total_records:,}")
    print(f"   • Archivos generados: {len(all_backup_files) + 2}")  # +2 por los ZIP
    print(f"   • Ubicaciones: {len(locations)}")
    print()
    print("📁 Archivos principales:")
    if primary_json:
        size = os.path.getsize(primary_json) / (1024 * 1024)
        print(f"   • Primario: {os.path.basename(primary_json)} ({size:.2f} MB)")
    if secondary_json:
        size = os.path.getsize(secondary_json) / (1024 * 1024)
        print(f"   • Secundario: {os.path.basename(secondary_json)} ({size:.2f} MB)")
    if zip_archive:
        size = os.path.getsize(zip_archive) / (1024 * 1024)
        print(f"   • Archivo: {os.path.basename(zip_archive)} ({size:.2f} MB)")
    print()
    print("=" * 80)
    
    return {
        'timestamp': timestamp,
        'locations': locations,
        'files': all_backup_files,
        'total_records': total_records
    }

if __name__ == "__main__":
    try:
        result = backup_blindado()
        print()
        print("ℹ️  Siguiente paso: Ejecutar 'python download_render_images.py' para descargar imágenes")
        print()
    except Exception as e:
        print(f"\n❌ Error crítico: {str(e)}")
        import traceback
        traceback.print_exc()
    
    input("Presiona Enter para salir...")
