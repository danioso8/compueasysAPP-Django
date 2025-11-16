import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from django.db import connection

# Verificar tablas de contable
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'contable_%'
        ORDER BY tablename
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"✓ Encontradas {len(tables)} tablas de contable:\n")
    for table in tables:
        # Contar registros
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"  {'✓' if 'user' in table.lower() else ' '} {table:40} ({count} registros)")
    
    # Verificar específicamente contable_user
    if 'contable_user' in tables:
        print("\n✅ La tabla contable_user existe!")
        cursor.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position', ['contable_user'])
        columns = cursor.fetchall()
        print("\nColumnas de contable_user:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
    else:
        print("\n❌ La tabla contable_user NO existe")
