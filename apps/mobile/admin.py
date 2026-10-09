from django.contrib import admin
from .models import AcessoApp, ConfiguracaoApp, MensagemApp, PalavraDoDia, PedidoOracao, PushSubscription

@admin.register(ConfiguracaoApp)
class ConfiguracaoAppAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'nome_exibicao', 'ativo', 'cidade', 'uf')
    list_filter = ('ativo', 'uf')
    search_fields = ('igreja__nome', 'nome_app', 'nome_exibicao', 'cidade')
    fieldsets = (('Aplicativo', {'fields': ('igreja', 'ativo', 'nome_app', 'nome_exibicao', 'descricao', 'mensagem_boas_vindas')}), ('Identidade visual', {'fields': ('logo', 'banner_principal')}), ('Contato e redes sociais', {'fields': ('telefone', 'whatsapp', 'instagram', 'youtube')}), ('Localização', {'fields': ('endereco', 'bairro', 'cidade', 'uf', 'cep', 'latitude', 'longitude', 'horarios_cultos')}))

@admin.register(PedidoOracao)
class PedidoOracaoAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'nome', 'telefone', 'atendido', 'criado_em')
    list_filter = ('igreja', 'atendido', 'criado_em')
    search_fields = ('nome', 'telefone', 'pedido')
    readonly_fields = ('criado_em',)
@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'endpoint_resumido', 'ativo', 'ultimo_uso_em', 'updated_at')
    list_filter = ('igreja', 'ativo')
    search_fields = ('igreja__nome', 'endpoint', 'user_agent')
    readonly_fields = ('endpoint', 'p256dh', 'auth', 'user_agent', 'ultimo_uso_em', 'created_at', 'updated_at')

    @admin.display(description='Endpoint')
    def endpoint_resumido(self, obj):
        return f'{obj.endpoint[:55]}…'
@admin.register(MensagemApp)
class MensagemAppAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'data', 'titulo', 'ativo', 'youtube_url')
    list_filter = ('igreja', 'ativo', 'data')
    search_fields = ('titulo', 'descricao', 'youtube_url')
    date_hierarchy = 'data'
    list_editable = ('ativo',)
    fields = ('igreja', 'data', 'titulo', 'youtube_url', 'descricao', 'ativo')
@admin.register(AcessoApp)
class AcessoAppAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'evento', 'recurso', 'visitante_id', 'dispositivo', 'acessado_em')
    list_filter = ('igreja', 'canal', 'evento', 'dispositivo', 'acessado_em')
    search_fields = ('igreja__nome', 'visitante_id', 'recurso', 'evento')
    date_hierarchy = 'acessado_em'
    readonly_fields = ('igreja', 'visitante_id', 'usuario', 'canal', 'evento', 'recurso', 'dispositivo', 'user_agent', 'dados', 'acessado_em')