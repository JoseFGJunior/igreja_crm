from django.contrib import admin
from apps.membros.models import Membro


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
