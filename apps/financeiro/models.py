from django.db import models
from django.conf import settings

from apps.core.models import TenantModel


class CategoriaFinanceira(TenantModel):

    TIPO_ENTRADA = 'ENTRADA'
    TIPO_SAIDA = 'SAIDA'

    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saida'),
    ]

    nome = models.CharField(
        max_length=100
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES
    )

    ativa = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Categoria financeira'
        verbose_name_plural = 'Categorias financeiras'
        ordering = (
            'tipo',
            'nome',
        )
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'igreja',
                    'tipo',
                    'nome',
                ],
                name='categoria_financeira_unica_por_igreja_tipo'
            )
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.nome}'


class LancamentoFinanceiro(TenantModel):

    TIPO_ENTRADA = 'ENTRADA'
    TIPO_SAIDA = 'SAIDA'

    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saida'),
    ]

    FORMA_DINHEIRO = 'DINHEIRO'
    FORMA_PIX = 'PIX'
    FORMA_CARTAO = 'CARTAO'
    FORMA_TRANSFERENCIA = 'TRANSFERENCIA'
    FORMA_BOLETO = 'BOLETO'
    FORMA_OUTRO = 'OUTRO'

    FORMA_PAGAMENTO_CHOICES = [
        (FORMA_DINHEIRO, 'Dinheiro'),
        (FORMA_PIX, 'Pix'),
        (FORMA_CARTAO, 'Cartao'),
        (FORMA_TRANSFERENCIA, 'Transferencia'),
        (FORMA_BOLETO, 'Boleto'),
        (FORMA_OUTRO, 'Outro'),
    ]

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES
    )

    categoria = models.ForeignKey(
        CategoriaFinanceira,
        on_delete=models.PROTECT,
        related_name='lancamentos'
    )

    membro = models.ForeignKey(
        'membros.Membro',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='lancamentos_financeiros'
    )

    descricao = models.CharField(
        max_length=200
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    data = models.DateField()

    data_emissao = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de emissão'
    )

    data_pagamento = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de pagamento'
    )

    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        default=FORMA_PIX
    )

    observacao = models.TextField(
        blank=True,
        null=True
    )

    grupo_recorrencia = models.UUIDField(
        blank=True,
        null=True,
        db_index=True
    )

    numero_parcela = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )

    total_parcelas = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Lancamento financeiro'
        verbose_name_plural = 'Lancamentos financeiros'
        ordering = (
            '-data',
            '-id',
        )
        indexes = [
            models.Index(
                fields=[
                    'igreja',
                    'data',
                ]
            ),
            models.Index(
                fields=[
                    'igreja',
                    'tipo',
                ]
            ),
        ]

    def __str__(self):
        return f'{self.data:%d/%m/%Y} - {self.descricao} - {self.valor}'

    @property
    def parcela_display(self):
        if not self.numero_parcela or not self.total_parcelas:
            return ''

        return f'{self.numero_parcela}/{self.total_parcelas}'


class FechamentoFinanceiroMensal(TenantModel):
    """Consolidação auditável; os lançamentos continuam sendo a fonte dos valores."""

    STATUS_ABERTO = 'ABERTO'
    STATUS_FECHADO = 'FECHADO'
    STATUS_CHOICES = [(STATUS_ABERTO, 'Aberto'), (STATUS_FECHADO, 'Fechado')]

    ORIGEM_IMPLANTACAO = 'IMPLANTACAO'
    ORIGEM_ANTERIOR = 'FECHAMENTO_ANTERIOR'
    ORIGEM_CHOICES = [
        (ORIGEM_IMPLANTACAO, 'Saldo inicial de implantação'),
        (ORIGEM_ANTERIOR, 'Saldo final da competência anterior'),
    ]

    competencia = models.DateField(help_text='Primeiro dia do mês de referência.')
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    origem_saldo_inicial = models.CharField(max_length=24, choices=ORIGEM_CHOICES)
    total_receitas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_despesas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ABERTO)
    fechado_em = models.DateTimeField(blank=True, null=True)
    fechado_por = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name='fechamentos_realizados')
    reaberto_em = models.DateTimeField(blank=True, null=True)
    reaberto_por = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name='fechamentos_reabertos')

    class Meta:
        verbose_name = 'Fechamento financeiro mensal'
        verbose_name_plural = 'Fechamentos financeiros mensais'
        ordering = ('-competencia',)
        constraints = [models.UniqueConstraint(fields=['igreja', 'competencia'], name='fechamento_unico_por_igreja_competencia')]
        permissions = [
            ('fechar_mes', 'Pode fechar competência financeira'),
            ('reabrir_mes', 'Pode reabrir competência financeira'),
            ('configurar_saldo_inicial', 'Pode configurar saldo inicial de implantação'),
            ('imprimir_fechamento', 'Pode imprimir fechamento financeiro'),
        ]

    def __str__(self):
        return f'{self.igreja} - {self.competencia:%m/%Y}'
