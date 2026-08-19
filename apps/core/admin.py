from django.contrib import admin

from apps.core.models import AcaoMissionaria


@admin.register(AcaoMissionaria)
class AcaoMissionariaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'titulo',
        'data_acao',
        'local',
        'destaque',
        'ativo',
    )
    list_filter = (
        'ativo',
        'destaque',
        'data_acao',
    )
    search_fields = (
        'titulo',
        'descricao',
        'local',
    )
