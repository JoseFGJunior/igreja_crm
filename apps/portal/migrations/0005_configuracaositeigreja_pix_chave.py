from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('portal', '0004_configuracaositeigreja_destino_publico_url_app_web')]
    operations = [
        migrations.AddField(
            model_name='configuracaositeigreja',
            name='pix_chave',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
