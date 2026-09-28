from django.db import models
from apps.core.models import TenantModel

class ConfiguracaoApp(TenantModel):
    ativo = models.BooleanField(default=False)
    nome_app = models.CharField(max_length=150, blank=True)
    nome_exibicao = models.CharField(max_length=150, blank=True)
    descricao = models.TextField(blank=True)
    logo = models.ImageField(upload_to='mobile/logos/', blank=True, null=True)
    banner_principal = models.ImageField(upload_to='mobile/banners/', blank=True, null=True)
    mensagem_boas_vindas = models.TextField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    horarios_cultos = models.TextField(blank=True)
    class Meta:
        verbose_name = 'Configuração do aplicativo'
        verbose_name_plural = 'Configuração do aplicativo'
        constraints = [models.UniqueConstraint(fields=('igreja',), name='unique_mobile_config_igreja')]
    def __str__(self):
        return self.nome_exibicao or self.nome_app or self.igreja.nome

class PalavraDoDia(TenantModel):
    STATUS_RASCUNHO = 'RASCUNHO'
    STATUS_AGUARDANDO_APROVACAO = 'AGUARDANDO_APROVACAO'
    STATUS_APROVADO = 'APROVADO'
    STATUS_PUBLICADO = 'PUBLICADO'
    STATUS_CHOICES = [(STATUS_RASCUNHO, 'Rascunho'), (STATUS_AGUARDANDO_APROVACAO, 'Aguardando aprovação'), (STATUS_APROVADO, 'Aprovado'), (STATUS_PUBLICADO, 'Publicado')]
    data = models.DateField()
    titulo = models.CharField(max_length=200)
    referencia_biblica = models.CharField(max_length=255, blank=True)
    texto_biblico = models.TextField(blank=True)
    reflexao = models.TextField(blank=True)
    aplicacao = models.TextField(blank=True)
    oracao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to='mobile/palavras-do-dia/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    publicado = models.BooleanField(default=False)
    class Meta:
        verbose_name = 'Palavra do dia'
        verbose_name_plural = 'Palavras do dia'
        ordering = ('-data', '-id')
        constraints = [models.UniqueConstraint(fields=('igreja', 'data'), name='unique_palavra_dia_igreja_data')]
    def __str__(self):
        return f'{self.data:%d/%m/%Y} - {self.titulo}'
class PedidoOracao(TenantModel):
    nome = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=30)
    pedido = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    atendido = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Pedido de oração'
        verbose_name_plural = 'Pedidos de oração'
        ordering = ('-criado_em',)

    def __str__(self):
        return f'{self.nome or "Anônimo"} · {self.criado_em:%d/%m/%Y %H:%M}'