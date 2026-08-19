from django.contrib import admin
from apps.igrejas.models import Igreja


@admin.register(Igreja)
class IgrejaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'nome',
        'slug',
        'plano',
        'ativa',
    )

    search_fields = (
        'nome',
        'slug',
    )

    list_filter = (
        'plano',
        'ativa',
    )
