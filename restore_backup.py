"""
Script para restaurar backup de la base de datos Django
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
from django.core.management import call_command

def list_backups():
    """Listar todos los backups disponibles"""
    
    BASE_DIR = Path(__file__).resolve().parent
    backup_dir = os.path.join(BASE_DIR, 'backups')
    
    if not os.path.exists(backup_dir):
        return []
    
    # Buscar archivos de backup
    backups = []
    for file in os.listdir(backup_dir):
        if file.endswith('.json') and 'backup' in file:
            file_path = os.path.join(backup_dir, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            file_time = os.path.getmtime(file_path)
            
            backups.append({
                'name': file,
                'path': file_path,
                'size': file_size,
                'date': datetime.fromtimestamp(file_time)
            })
    
    return sorted(backups, key=lambda x: x['date'], reverse=True)

def restore_backup(backup_file):
    """Restaurar backup desde archivo JSON"""
    
    print("=" * 70)
    print("🔄 RESTAURANDO BACKUP")
    print("=" * 70)
    print()
    print(f"📁 Archivo: {backup_file}")
    print()
    
    # Confirmar
    print("⚠️  ADVERTENCIA: Esta operación puede sobrescribir datos existentes")
    confirm = input("¿Deseas continuar? (escribe 'SI' para confirmar): ")
    
    if confirm.upper() != 'SI':
        print("❌ Operación cancelada")
        return False
    
    print()
    print("⏳ Restaurando datos...")
    
    try:
        # Cargar datos del backup
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        # Deserializar
        objects = serializers.deserialize('json', data)
        
        restored_count = 0
        for obj in objects:
            try:
                obj.save()
                restored_count += 1
            except Exception as e:
                print(f"⚠️  Error al restaurar {obj}: {str(e)}")
        
        print()
        print("=" * 70)
        print(f"✅ Restauración completada: {restored_count} registros restaurados")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al restaurar: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def restore_using_loaddata(backup_file):
    """Restaurar usando el comando loaddata de Django"""
    
    print("=" * 70)
    print("🔄 RESTAURANDO USANDO LOADDATA")
    print("=" * 70)
    print()
    
    try:
        call_command('loaddata', backup_file, verbosity=2)
        
        print()
        print("=" * 70)
        print("✅ Restauración completada exitosamente")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("🗄️  RESTAURAR BACKUP - COMPUEASYS")
    print("=" * 70)
    print()
    
    # Listar backups disponibles
    backups = list_backups()
    
    if not backups:
        print("❌ No se encontraron backups disponibles")
        print("   Los backups deben estar en la carpeta 'backups/'")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    print("📦 Backups disponibles:\n")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup['name']}")
        print(f"   📅 Fecha: {backup['date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📊 Tamaño: {backup['size']:.2f} MB")
        print()
    
    # Seleccionar backup
    try:
        choice = input(f"Selecciona un backup (1-{len(backups)}): ").strip()
        index = int(choice) - 1
        
        if 0 <= index < len(backups):
            selected_backup = backups[index]
            restore_backup(selected_backup['path'])
        else:
            print("❌ Selección inválida")
            
    except ValueError:
        print("❌ Entrada inválida")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()
    input("Presiona Enter para salir...")
