from django.contrib import admin
from .models import ConfiguracaoApp, PalavraDoDia, PedidoOracao

@admin.register(ConfiguracaoApp)
class ConfiguracaoAppAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'nome_exibicao', 'ativo', 'cidade', 'uf')
    list_filter = ('ativo', 'uf')
    search_fields = ('igreja__nome', 'nome_app', 'nome_exibicao', 'cidade')
    fieldsets = (('Aplicativo', {'fields': ('igreja', 'ativo', 'nome_app', 'nome_exibicao', 'descricao', 'mensagem_boas_vindas')}), ('Identidade visual', {'fields': ('logo', 'banner_principal')}), ('Contato e redes sociais', {'fields': ('telefone', 'whatsapp', 'instagram', 'youtube')}), ('Localização', {'fields': ('endereco', 'bairro', 'cidade', 'uf', 'cep', 'latitude', 'longitude', 'horarios_cultos')}))

@admin.register(PalavraDoDia)
class PalavraDoDiaAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'data', 'titulo', 'status', 'publicado')
    list_filter = ('igreja', 'status', 'publicado', 'data')
    search_fields = ('titulo', 'referencia_biblica', 'texto_biblico', 'reflexao')
    date_hierarchy = 'data'
@admin.register(PedidoOracao)
class PedidoOracaoAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'nome', 'telefone', 'atendido', 'criado_em')
    list_filter = ('igreja', 'atendido', 'criado_em')
    search_fields = ('nome', 'telefone', 'pedido')
    readonly_fields = ('criado_em',)