from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lancamentofinanceiro',
            name='grupo_recorrencia',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='lancamentofinanceiro',
            name='numero_parcela',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lancamentofinanceiro',
            name='total_parcelas',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
