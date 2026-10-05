from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('portal', '0003_remove_horarios_texto_default')]
    operations = [
        migrations.AddField(
            model_name='configuracaositeigreja',
            name='destino_publico',
            field=models.CharField(choices=[('PORTAL', 'Portal institucional'), ('APP', 'Aplicativo web')], default='PORTAL', max_length=10),
        ),
        migrations.AddField(
            model_name='configuracaositeigreja',
            name='url_app_web',
            field=models.URLField(blank=True),
        ),
    ]
