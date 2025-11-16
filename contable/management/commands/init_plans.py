from django.core.management.base import BaseCommand
from contable.models import Plan


class Command(BaseCommand):
    help = 'Inicializa los planes de suscripción del sistema contable'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Inicializando planes de suscripción...'))

        # Plan Gratuito
        free_plan, created = Plan.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Plan Gratuito',
                'price': 0,
                'max_users': 1,
                'max_companies': 1,
                'max_invoices_month': 50,
                'features': {
                    'modules': ['invoicing', 'customers', 'reports_basic'],
                    'storage_gb': 1,
                    'support': 'email',
                    'features': [
                        'Facturación básica',
                        'Gestión de clientes',
                        'Reportes básicos',
                        '1 GB de almacenamiento'
                    ]
                },
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Plan Gratuito creado'))
        else:
            self.stdout.write(self.style.WARNING('  Plan Gratuito ya existe'))

        # Plan Profesional
        pro_plan, created = Plan.objects.get_or_create(
            name='pro',
            defaults={
                'display_name': 'Plan Profesional',
                'price': 99900,
                'max_users': 5,
                'max_companies': 3,
                'max_invoices_month': 500,
                'features': {
                    'modules': [
                        'invoicing', 'customers', 'suppliers', 'products',
                        'inventory', 'purchases', 'accounting', 'reports_advanced',
                        'payroll', 'fixed_assets'
                    ],
                    'storage_gb': 10,
                    'support': 'priority',
                    'features': [
                        'Todos los módulos incluidos',
                        'Reportes avanzados',
                        'Inventario con FIFO/LIFO',
                        'Nómina completa',
                        'Activos fijos',
                        '10 GB de almacenamiento',
                        'Soporte prioritario'
                    ]
                },
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Plan Profesional creado'))
        else:
            self.stdout.write(self.style.WARNING('  Plan Profesional ya existe'))

        # Plan Empresarial
        enterprise_plan, created = Plan.objects.get_or_create(
            name='enterprise',
            defaults={
                'display_name': 'Plan Empresarial',
                'price': 299900,
                'max_users': -1,  # Ilimitado
                'max_companies': -1,  # Ilimitado
                'max_invoices_month': -1,  # Ilimitado
                'features': {
                    'modules': 'all',
                    'storage_gb': 100,
                    'support': '24/7',
                    'features': [
                        'Todo ilimitado',
                        'Multi-empresa sin límites',
                        'Usuarios ilimitados',
                        'Facturación electrónica',
                        'API personalizada',
                        'Integraciones avanzadas',
                        '100 GB de almacenamiento',
                        'Soporte 24/7',
                        'Consultor asignado',
                        'Capacitación incluida'
                    ]
                },
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Plan Empresarial creado'))
        else:
            self.stdout.write(self.style.WARNING('  Plan Empresarial ya existe'))

        self.stdout.write(self.style.SUCCESS('\n✓ Inicialización completada exitosamente'))
        
        self.stdout.write('\nPlanes disponibles:')
        for plan in Plan.objects.filter(is_active=True):
            self.stdout.write(f'  • {plan.display_name}: ${plan.price:,.0f}/mes')
