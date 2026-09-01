from django.contrib import admin

from apps.eventos.models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'igreja', 'titulo', 'data', 'hora_inicio', 'categoria', 'local')
    list_filter = ('igreja', 'categoria', 'data')
    search_fields = ('titulo', 'descricao', 'observacoes', 'local')
    date_hierarchy = 'data'
