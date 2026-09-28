# Remove the old fixed worship-schedule text. Each church now supplies this
# content exclusively through Configuração do Site da Igreja > Horários texto.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0002_configuracaositeigreja_descricao_contribuicao_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuracaositeigreja',
            name='horarios_texto',
            field=models.TextField(blank=True),
        ),
    ]
