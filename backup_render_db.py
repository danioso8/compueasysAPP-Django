"""
Script para hacer backup de la base de datos PostgreSQL de Render
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

def backup_database():
    """Crear backup de la base de datos de Render"""
    
    # Obtener credenciales de la base de datos
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    
    # Verificar que tenemos todas las credenciales
    if not all([db_name, db_user, db_password, db_host]):
        print("❌ Error: No se encontraron todas las credenciales de la base de datos")
        print("   Asegúrate de tener las siguientes variables en tu archivo .env:")
        print("   - DB_NAME")
        print("   - DB_USERNAME")
        print("   - DB_PASSWORD")
        print("   - DB_HOST")
        print("   - DB_PORT (opcional, default: 5432)")
        return False
    
    # Crear directorio de backups si no existe
    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nombre del archivo de backup con fecha y hora
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'compueasys_backup_{timestamp}.sql')
    
    print("🔄 Iniciando backup de la base de datos...")
    print(f"📦 Base de datos: {db_name}")
    print(f"🖥️  Host: {db_host}")
    print(f"💾 Archivo destino: {backup_file}")
    
    # Configurar variable de entorno para la contraseña
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password
    
    # Comando pg_dump
    command = [
        'pg_dump',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-d', db_name,
        '-F', 'p',  # Formato plain (SQL)
        '-f', backup_file,
        '--no-owner',  # No incluir comandos de propiedad
        '--no-privileges',  # No incluir comandos de privilegios
        '-v'  # Verbose
    ]
    
    try:
        # Ejecutar pg_dump
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\n✅ ¡Backup completado exitosamente!")
        print(f"📁 Archivo guardado en: {backup_file}")
        
        # Mostrar tamaño del archivo
        file_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB
        print(f"📊 Tamaño del archivo: {file_size:.2f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al realizar el backup:")
        print(f"   {e.stderr}")
        return False
    except FileNotFoundError:
        print("\n❌ Error: No se encontró el comando 'pg_dump'")
        print("   Necesitas instalar PostgreSQL client tools:")
        print("   - Windows: Descarga PostgreSQL desde https://www.postgresql.org/download/windows/")
        print("   - Durante la instalación, asegúrate de instalar 'Command Line Tools'")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        return False

def backup_with_custom_format():
    """Crear backup en formato custom (comprimido) de PostgreSQL"""
    
    # Obtener credenciales de la base de datos
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    
    if not all([db_name, db_user, db_password, db_host]):
        print("❌ Error: No se encontraron todas las credenciales")
        return False
    
    # Crear directorio de backups
    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nombre del archivo de backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'compueasys_backup_{timestamp}.dump')
    
    print("🔄 Iniciando backup comprimido...")
    print(f"📦 Base de datos: {db_name}")
    print(f"💾 Archivo destino: {backup_file}")
    
    # Configurar variable de entorno para la contraseña
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password
    
    # Comando pg_dump con formato custom
    command = [
        'pg_dump',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-d', db_name,
        '-F', 'c',  # Formato custom (comprimido)
        '-f', backup_file,
        '--no-owner',
        '--no-privileges',
        '-v'
    ]
    
    try:
        subprocess.run(command, env=env, capture_output=True, text=True, check=True)
        
        print("\n✅ ¡Backup comprimido completado!")
        print(f"📁 Archivo guardado en: {backup_file}")
        
        file_size = os.path.getsize(backup_file) / (1024 * 1024)
        print(f"📊 Tamaño del archivo: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🗄️  BACKUP BASE DE DATOS COMPUEASYS - RENDER")
    print("=" * 60)
    print()
    
    print("Selecciona el formato de backup:")
    print("1. SQL (formato texto, fácil de leer)")
    print("2. DUMP (formato comprimido, ocupa menos espacio)")
    print("3. Ambos formatos")
    
    choice = input("\nElige una opción (1/2/3) [1]: ").strip() or "1"
    
    print()
    
    if choice == "1":
        backup_database()
    elif choice == "2":
        backup_with_custom_format()
    elif choice == "3":
        backup_database()
        print("\n" + "-" * 60 + "\n")
        backup_with_custom_format()
    else:
        print("❌ Opción inválida")
    
    print("\n" + "=" * 60)
    input("\nPresiona Enter para salir...")
