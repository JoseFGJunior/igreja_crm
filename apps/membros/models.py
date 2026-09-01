from django.conf import settings
from django.db import models
from django.db.models import Q
from apps.core.models import TenantModel


class Membro(TenantModel):

    STATUS_CHOICES = [
        ('MEMBRO', 'Membro'),
        ('CONGREGADO', 'Congregado'),
        ('VISITANTE', 'Visitante'),
        ('INATIVO', 'Inativo'),
    ]

    CUIDADO_IDOSO = 'IDOSO'
    CUIDADO_SAUDE = 'SAUDE'
    CUIDADO_FINANCEIRO = 'FINANCEIRO'
    CUIDADO_LUTO = 'LUTO'
    CUIDADO_MOBILIDADE = 'MOBILIDADE'
    CUIDADO_FAMILIAR = 'FAMILIAR'
    CUIDADO_OUTRO = 'OUTRO'

    TIPO_CUIDADO_CHOICES = [
        (CUIDADO_IDOSO, 'Idoso'),
        (CUIDADO_SAUDE, 'Saude / doenca'),
        (CUIDADO_FINANCEIRO, 'Carencia financeira'),
        (CUIDADO_LUTO, 'Luto'),
        (CUIDADO_MOBILIDADE, 'Mobilidade reduzida'),
        (CUIDADO_FAMILIAR, 'Acompanhamento familiar'),
        (CUIDADO_OUTRO, 'Outro'),
    ]

    PRIORIDADE_BAIXA = 'BAIXA'
    PRIORIDADE_MEDIA = 'MEDIA'
    PRIORIDADE_ALTA = 'ALTA'
    PRIORIDADE_URGENTE = 'URGENTE'

    PRIORIDADE_CUIDADO_CHOICES = [
        (PRIORIDADE_BAIXA, 'Baixa'),
        (PRIORIDADE_MEDIA, 'Media'),
        (PRIORIDADE_ALTA, 'Alta'),
        (PRIORIDADE_URGENTE, 'Urgente'),
    ]

    STATUS_VISITANTE_CHOICES = [
        ('NOVO', 'Novo'),
        ('ACOMPANHAMENTO', 'Em acompanhamento'),
        ('RETORNOU', 'Retornou'),
        ('FREQUENTE', 'Frequente'),
        ('INTEGRADO', 'Integrado'),
        ('SEM_RETORNO', 'Sem retorno'),
    ]

    nome = models.CharField(
        max_length=200
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    data_primeira_visita = models.DateField(
        blank=True,
        null=True
    )

    origem_visitante = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    observacao_visitante = models.TextField(
        blank=True,
        null=True
    )

    status_visitante = models.CharField(
        max_length=30,
        choices=STATUS_VISITANTE_CHOICES,
        default='NOVO'
    )

    responsavel_visitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitantes_responsaveis'
    )

    data_nascimento = models.DateField(
        blank=True,
        null=True
    )

    endereco = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    bairro = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='MEMBRO'
    )

    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    batizado = models.BooleanField(
        default=False
    )

    data_batismo = models.DateField(
        blank=True,
        null=True
    )

    necessita_cuidado_especial = models.BooleanField(
        default=False
    )

    tipo_cuidado_especial = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    prioridade_cuidado = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CUIDADO_CHOICES,
        blank=True,
        null=True
    )

    responsavel_cuidado = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    observacao_cuidado_especial = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Membro'
        verbose_name_plural = 'Membros'

    def __str__(self):
        return self.nome

    def get_tipos_cuidado_especial(self):
        if not self.tipo_cuidado_especial:
            return []

        tipos = [
            tipo.strip()
            for tipo in self.tipo_cuidado_especial.split(',')
            if tipo.strip()
        ]

        labels = dict(self.TIPO_CUIDADO_CHOICES)
        return [
            labels.get(tipo, tipo)
            for tipo in tipos
        ]

    def get_tipos_cuidado_especial_display(self):
        tipos = self.get_tipos_cuidado_especial()

        if not tipos:
            return '-'

        return ', '.join(tipos)


class VisitaVisitante(TenantModel):

    visitante = models.ForeignKey(
        Membro,
        on_delete=models.CASCADE,
        related_name='visitas_visitante'
    )

    data_visita = models.DateField()
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ('data_visita', 'id')


class AcompanhamentoVisitante(TenantModel):

    TIPO_CHOICES = [
        ('24H', 'Contato de 24 horas'),
        ('7D', 'Contato de 7 dias'),
        ('15D', 'Contato de 15 dias'),
        ('RETORNO', 'Nova tentativa'),
    ]

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    visitante = models.ForeignKey(
        Membro,
        on_delete=models.CASCADE,
        related_name='acompanhamentos_visitante'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data_prevista = models.DateField()
    data_realizada = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acompanhamentos_visitante_responsaveis'
    )
    resultado = models.CharField(max_length=100, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ('data_prevista', 'id')
        constraints = [
            models.UniqueConstraint(
                fields=('visitante', 'tipo'),
                condition=Q(tipo__in=('24H', '7D', '15D')),
                name='unique_jornada_visitante_tipo'
            )
        ]


class MensagemWhatsAppVisitante(TenantModel):

    TIPO_CHOICES = (
        ('24H', 'Mensagem de 24 horas'),
        ('7D', 'Mensagem de 7 dias'),
        ('15D', 'Mensagem de 15 dias'),
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensagem = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('igreja', 'tipo'),
                name='unique_mensagem_whatsapp_igreja_tipo'
            )
        ]
