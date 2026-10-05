from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [('mobile', '0004_mensagemapp')]

    operations = [
        migrations.AddField(
            model_name='mensagemapp',
            name='data',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]