from django.contrib import admin

from .models import (
    AvisoIgreja,
    BannerSiteIgreja,
    ConfiguracaoSiteIgreja,
    ProgramacaoIgreja,
)


@admin.register(ConfiguracaoSiteIgreja)
class ConfiguracaoSiteIgrejaAdmin(admin.ModelAdmin):
    list_display = ('igreja', 'titulo_site', 'site_ativo', 'transmissao_url')
    list_filter = ('site_ativo',)
    search_fields = ('igreja__nome', 'titulo_site')
    fieldsets = (
        ('Identidade e aparência', {'fields': ('igreja', 'titulo_site', 'descricao', 'slogan', 'slug_publico', 'dominio_personalizado', 'logo', 'imagem_capa', 'imagem_padrao', 'cor_primaria', 'cor_secundaria', 'cor_destaque')}),
        ('Contato e redes sociais', {'fields': ('telefone', 'whatsapp', 'email_publico', 'endereco', 'bairro', 'cidade', 'estado', 'instagram', 'facebook', 'youtube')}),
        ('Transmissão, horários e contribuição', {'fields': ('transmissao_url', 'horarios_texto', 'pix_imagem')}),
        ('Cards de ações', {'fields': ('texto_visitar', 'descricao_visitar', 'texto_oracao', 'descricao_oracao', 'texto_transmissao', 'descricao_transmissao', 'texto_contribuicao', 'descricao_contribuicao')}),
        ('Sobre e pastor', {'fields': ('texto_sobre', 'foto_pastor', 'nome_pastor', 'descricao_pastor')}),
        ('Exibição', {'fields': ('site_ativo', 'exibir_eventos', 'exibir_programacao', 'exibir_avisos', 'exibir_pastor', 'exibir_redes_sociais')}),
    )


admin.site.register(BannerSiteIgreja)
admin.site.register(ProgramacaoIgreja)
admin.site.register(AvisoIgreja)