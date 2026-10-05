from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('mobile', '0003_pushsubscription')]
    operations = [
        migrations.CreateModel(
            name='MensagemApp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('titulo', models.CharField(max_length=200)),
                ('descricao', models.TextField(blank=True)),
                ('youtube_url', models.URLField()),
                ('imagem', models.ImageField(blank=True, null=True, upload_to='mobile/mensagens/')),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('ativo', models.BooleanField(default=True)),
                ('igreja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='igrejas.igreja')),
            ],
            options={'verbose_name': 'Mensagem do aplicativo', 'verbose_name_plural': 'Mensagens do aplicativo', 'ordering': ('ordem', '-created_at')},
        ),
    ]
