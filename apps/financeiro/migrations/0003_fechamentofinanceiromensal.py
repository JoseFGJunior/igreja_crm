from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('financeiro', '0002_lancamentofinanceiro_recorrencia')]

    operations = [
        migrations.CreateModel(
            name='FechamentoFinanceiroMensal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('competencia', models.DateField(help_text='Primeiro dia do mês de referência.')),
                ('saldo_inicial', models.DecimalField(decimal_places=2, max_digits=12)),
                ('origem_saldo_inicial', models.CharField(choices=[('IMPLANTACAO', 'Saldo inicial de implantação'), ('FECHAMENTO_ANTERIOR', 'Saldo final da competência anterior')], max_length=24)),
                ('total_receitas', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_despesas', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('saldo_final', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('ABERTO', 'Aberto'), ('FECHADO', 'Fechado')], default='ABERTO', max_length=10)),
                ('fechado_em', models.DateTimeField(blank=True, null=True)),
                ('reaberto_em', models.DateTimeField(blank=True, null=True)),
                ('fechado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fechamentos_realizados', to=settings.AUTH_USER_MODEL)),
                ('igreja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='igrejas.igreja')),
                ('reaberto_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fechamentos_reabertos', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Fechamento financeiro mensal', 'verbose_name_plural': 'Fechamentos financeiros mensais', 'ordering': ('-competencia',), 'permissions': [('fechar_mes', 'Pode fechar competência financeira'), ('reabrir_mes', 'Pode reabrir competência financeira'), ('configurar_saldo_inicial', 'Pode configurar saldo inicial de implantação'), ('imprimir_fechamento', 'Pode imprimir fechamento financeiro')]},
        ),
        migrations.AddConstraint(model_name='fechamentofinanceiromensal', constraint=models.UniqueConstraint(fields=('igreja', 'competencia'), name='fechamento_unico_por_igreja_competencia')),
    ]
