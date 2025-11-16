#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppCompueasys.settings')
django.setup()

from contable.models import ContableUser, Plan, Company, UserProfile, CompanyMembership, AuditLog

print("\n" + "=" * 80)
print("📊 DATOS REGISTRADOS EN EL SISTEMA CONTABLE")
print("=" * 80)

# PLANES
print("\n🎯 PLANES DE SUSCRIPCIÓN:")
print("-" * 80)
for plan in Plan.objects.all():
    print(f"\n  {plan.name.upper()}")
    print(f"    💰 Precio: ${plan.price:,.0f}")
    print(f"    🏢 Empresas máx: {plan.max_companies}")
    print(f"    👥 Usuarios máx: {plan.max_users}")
    print(f"    📄 Facturas/mes: {plan.max_invoices_month}")
    print(f"    ✓ Activo: {'Sí' if plan.is_active else 'No'}")

# USUARIOS
print("\n\n👥 USUARIOS CONTABLES:")
print("-" * 80)
users = ContableUser.objects.all()
if users.exists():
    for user in users:
        print(f"\n  📧 {user.email}")
        print(f"    ID: {user.id}")
        print(f"    Nombre: {user.get_full_name()}")
        print(f"    Teléfono: {user.phone or 'N/A'}")
        print(f"    Email verificado: {'✅ SÍ' if user.email_verified else '⚠️ NO'}")
        print(f"    Activo: {'✅' if user.is_active else '❌'}")
        print(f"    Fecha registro: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Último login: {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '❌ Nunca'}")
else:
    print("  ⚠️  No hay usuarios registrados")

# EMPRESAS
print("\n\n🏢 EMPRESAS:")
print("-" * 80)
companies = Company.objects.all()
if companies.exists():
    for company in companies:
        print(f"\n  🏢 {company.name}")
        print(f"    Razón Social: {company.legal_name}")
        print(f"    NIT/RUT: {company.tax_id}")
        print(f"    Email: {company.email}")
        print(f"    Teléfono: {company.phone or 'N/A'}")
        print(f"    Plan: {company.plan.name.upper()}")
        print(f"    Moneda: {company.currency}")
        print(f"    Activa: {'✅' if company.is_active else '❌'}")
        print(f"    Creada: {company.created_at.strftime('%Y-%m-%d %H:%M')}")
else:
    print("  ⚠️  No hay empresas registradas")

# MEMBRESÍAS
print("\n\n🔗 MEMBRESÍAS (Usuario-Empresa):")
print("-" * 80)
memberships = CompanyMembership.objects.all()
if memberships.exists():
    for m in memberships:
        default = " ⭐" if m.is_default else ""
        print(f"\n  {m.user_profile.user.get_full_name()} → {m.company.name}{default}")
        print(f"    Rol: {m.role_in_company}")
        print(f"    Fecha unión: {m.joined_at.strftime('%Y-%m-%d %H:%M')}")
else:
    print("  ⚠️  No hay membresías")

# AUDITORÍA
print("\n\n📋 ÚLTIMOS REGISTROS DE AUDITORÍA:")
print("-" * 80)
logs = AuditLog.objects.all().order_by('-timestamp')[:10]
if logs.exists():
    for log in logs:
        print(f"  [{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log.action.upper()}")
        print(f"    Usuario: {log.user.email if log.user else 'N/A'}")
        print(f"    Empresa: {log.company.name if log.company else 'N/A'}")
        print(f"    Módulo: {log.module}")
        print(f"    Descripción: {log.description}")
        print(f"    IP: {log.ip_address or 'N/A'}")
        print()
else:
    print("  ⚠️  No hay registros de auditoría")

# RESUMEN
print("=" * 80)
print("📈 RESUMEN GENERAL:")
print("=" * 80)
print(f"  📋 Planes: {Plan.objects.count()}")
print(f"  👤 Usuarios: {ContableUser.objects.count()}")
print(f"  ✅ Verificados: {ContableUser.objects.filter(email_verified=True).count()}")
print(f"  ⏳ Pendientes: {ContableUser.objects.filter(email_verified=False).count()}")
print(f"  🏢 Empresas: {Company.objects.count()}")
print(f"  ✅ Activas: {Company.objects.filter(is_active=True).count()}")
print(f"  🔗 Membresías: {CompanyMembership.objects.count()}")
print(f"  📝 Auditoría: {AuditLog.objects.count()} registros")
print("=" * 80 + "\n")
