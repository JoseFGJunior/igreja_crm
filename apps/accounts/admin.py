from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import Usuario, UsuarioIgreja


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    pass


@admin.register(UsuarioIgreja)
class UsuarioIgrejaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'usuario',
        'igreja',
        'igreja_default',
        'ativo',
    )

    list_filter = (
        'igreja_default',
        'ativo',
        'igreja',
    )

    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'igreja__nome',
    )
