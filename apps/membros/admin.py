from django.contrib import admin
from apps.membros.models import AcompanhamentoVisitante
from apps.membros.models import Membro
from apps.membros.models import VisitaVisitante


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'igreja',
        'nome',
        'status',
        'telefone',
        'necessita_cuidado_especial',
        'prioridade_cuidado',
    )
    list_filter = (
        'igreja',
        'status',
        'necessita_cuidado_especial',
        'prioridade_cuidado',
    )
    search_fields = (
        'nome',
        'telefone',
        'email',
        'responsavel_cuidado',
    )


@admin.register(VisitaVisitante)
class VisitaVisitanteAdmin(admin.ModelAdmin):
    list_display = ('visitante', 'igreja', 'data_visita')
    list_filter = ('igreja', 'data_visita')


@admin.register(AcompanhamentoVisitante)
class AcompanhamentoVisitanteAdmin(admin.ModelAdmin):
    list_display = ('visitante', 'igreja', 'tipo', 'data_prevista', 'status')
    list_filter = ('igreja', 'tipo', 'status')
