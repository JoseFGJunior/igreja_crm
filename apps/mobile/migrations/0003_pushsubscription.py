from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('mobile', '0002_pedidooracao')]
    operations = [
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('endpoint', models.URLField(max_length=2000, unique=True)),
                ('p256dh', models.TextField()),
                ('auth', models.TextField()),
                ('user_agent', models.TextField(blank=True)),
                ('ativo', models.BooleanField(default=True)),
                ('ultimo_uso_em', models.DateTimeField(blank=True, null=True)),
                ('igreja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='igrejas.igreja')),
            ],
            options={'verbose_name': 'Inscrição de notificação push', 'verbose_name_plural': 'Inscrições de notificações push', 'ordering': ('-updated_at',)},
        ),
    ]
