import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.db import connection

# Obtener todas las tablas que empiezan con contable_
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'contable_%'
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    if tables:
        print(f"Encontradas {len(tables)} tablas de contable:")
        for table in tables:
            print(f"  - {table}")
        
        # Eliminar todas las tablas
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                print(f"✓ Eliminada: {table}")
            except Exception as e:
                print(f"✗ Error eliminando {table}: {e}")
        
        connection.commit()
        print("\n✓ Todas las tablas de contable eliminadas")
    else:
        print("No se encontraron tablas de contable")
