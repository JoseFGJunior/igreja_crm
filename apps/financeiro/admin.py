from django.contrib import admin

from apps.financeiro.models import CategoriaFinanceira
from apps.financeiro.models import LancamentoFinanceiro
from apps.financeiro.models import FechamentoFinanceiroMensal


@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'igreja',
        'nome',
        'tipo',
        'ativa',
    )
    list_filter = (
        'igreja',
        'tipo',
        'ativa',
    )
    search_fields = (
        'nome',
        'igreja__nome',
    )


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'igreja',
        'data_emissao',
        'data',
        'data_pagamento',
        'tipo',
        'categoria',
        'descricao',
        'valor',
        'forma_pagamento',
        'membro',
    )
    list_filter = (
        'igreja',
        'tipo',
        'categoria',
        'forma_pagamento',
        'data_emissao',
        'data',
        'data_pagamento',
    )
    search_fields = (
        'descricao',
        'observacao',
        'membro__nome',
        'categoria__nome',
    )
    date_hierarchy = 'data'

@admin.register(FechamentoFinanceiroMensal)
class FechamentoFinanceiroMensalAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'competencia', 'status', 'saldo_inicial', 'total_receitas', 'total_despesas', 'saldo_final', 'fechado_em')
    list_filter = ('igreja', 'status', 'competencia')
    date_hierarchy = 'competencia'
