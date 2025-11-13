# Generated manually for admin notes field

from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('core', '0011_alter_pedido_options_pedido_codigo_descuento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='nota_admin',
            field=models.TextField(blank=True, null=True, help_text='Notas administrativas internas'),
        ),
    ]