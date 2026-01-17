"""
Script para hacer backup de la base de datos usando Django
(No requiere pg_dump instalado)
"""
import os
import json
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

def backup_database_django():
    """Crear backup usando Django dumpdata"""
    
    # Crear directorio de backups
    BASE_DIR = Path(__file__).resolve().parent
    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nombre del archivo de backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'compueasys_django_backup_{timestamp}.json')
    
    print("=" * 70)
    print("🗄️  BACKUP BASE DE DATOS COMPUEASYS - MÉTODO DJANGO")
    print("=" * 70)
    print()
    print("🔄 Iniciando backup usando Django...")
    print(f"💾 Archivo destino: {backup_file}")
    print()
    
    try:
        # Obtener todos los modelos
        all_models = apps.get_models()
        
        print("📦 Modelos a exportar:")
        app_models = {}
        for model in all_models:
            app_label = model._meta.app_label
            if app_label not in app_models:
                app_models[app_label] = []
            app_models[app_label].append(model._meta.model_name)
        
        for app, models in app_models.items():
            print(f"   • {app}: {', '.join(models)}")
        
        print()
        print("⏳ Exportando datos...")
        
        # Serializar todos los datos
        data = serializers.serialize('json', 
            [obj for model in all_models for obj in model.objects.all()],
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False
        )
        
        # Guardar en archivo
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(data)
        
        print()
        print("✅ ¡Backup completado exitosamente!")
        print(f"📁 Archivo guardado en: {backup_file}")
        
        # Mostrar tamaño del archivo
        file_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB
        print(f"📊 Tamaño del archivo: {file_size:.2f} MB")
        
        # Contar registros
        total_records = sum(model.objects.count() for model in all_models)
        print(f"📈 Total de registros exportados: {total_records:,}")
        
        print()
        print("=" * 70)
        print("ℹ️  Para restaurar este backup, usa: python restore_backup.py")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al realizar el backup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def backup_by_app():
    """Crear backups separados por app"""
    
    BASE_DIR = Path(__file__).resolve().parent
    backup_dir = os.path.join(BASE_DIR, 'backups')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("=" * 70)
    print("🗄️  BACKUP POR APLICACIÓN - COMPUEASYS")
    print("=" * 70)
    print()
    
    # Apps a exportar
    apps_to_backup = ['core', 'dashboard', 'contable', 'auth', 'contenttypes', 'sessions']
    
    for app_name in apps_to_backup:
        try:
            app_backup_file = os.path.join(backup_dir, f'{app_name}_backup_{timestamp}.json')
            
            print(f"📦 Exportando app: {app_name}...")
            
            # Obtener modelos de la app
            app_models = [m for m in apps.get_models() if m._meta.app_label == app_name]
            
            if not app_models:
                print(f"   ⚠️  No se encontraron modelos en {app_name}")
                continue
            
            # Serializar datos
            data = serializers.serialize('json',
                [obj for model in app_models for obj in model.objects.all()],
                indent=2
            )
            
            # Guardar
            with open(app_backup_file, 'w', encoding='utf-8') as f:
                f.write(data)
            
            file_size = os.path.getsize(app_backup_file) / 1024  # KB
            total_records = sum(model.objects.count() for model in app_models)
            
            print(f"   ✅ {app_name}: {total_records:,} registros ({file_size:.2f} KB)")
            
        except Exception as e:
            print(f"   ❌ Error en {app_name}: {str(e)}")
    
    print()
    print("=" * 70)
    print("✅ Backup por aplicación completado")
    print("=" * 70)

def show_db_stats():
    """Mostrar estadísticas de la base de datos"""
    
    print("=" * 70)
    print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
    print("=" * 70)
    print()
    
    # Información de conexión
    db_settings = connection.settings_dict
    print(f"🗄️  Base de datos: {db_settings.get('NAME', 'N/A')}")
    print(f"🖥️  Host: {db_settings.get('HOST', 'N/A')}")
    print(f"🔧 Engine: {db_settings.get('ENGINE', 'N/A')}")
    print()
    
    # Contar registros por modelo
    print("📈 Registros por modelo:")
    all_models = apps.get_models()
    
    app_stats = {}
    for model in all_models:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        count = model.objects.count()
        
        if app_label not in app_stats:
            app_stats[app_label] = []
        
        app_stats[app_label].append({
            'model': model_name,
            'count': count
        })
    
    for app, stats in sorted(app_stats.items()):
        print(f"\n   {app.upper()}:")
        for stat in stats:
            print(f"      • {stat['model']}: {stat['count']:,} registros")
    
    # Total
    total = sum(model.objects.count() for model in all_models)
    print()
    print("=" * 70)
    print(f"📊 TOTAL: {total:,} registros en la base de datos")
    print("=" * 70)

if __name__ == "__main__":
    print()
    
    # Mostrar estadísticas primero
    show_db_stats()
    
    print("\n")
    print("Selecciona el tipo de backup:")
    print("1. Backup completo (un solo archivo JSON)")
    print("2. Backup por aplicación (archivos separados)")
    print("3. Mostrar solo estadísticas (no hacer backup)")
    
    choice = input("\nElige una opción (1/2/3) [1]: ").strip() or "1"
    
    print()
    
    if choice == "1":
        backup_database_django()
    elif choice == "2":
        backup_by_app()
    elif choice == "3":
        print("✅ Estadísticas mostradas arriba")
    else:
        print("❌ Opción inválida")
    
    print()
    input("Presiona Enter para salir...")
