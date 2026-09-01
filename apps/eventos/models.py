from django.db import models

from apps.core.models import TenantModel


class Evento(TenantModel):
    CATEGORIA_CULTO = 'CULTO'
    CATEGORIA_REUNIAO = 'REUNIAO'
    CATEGORIA_EBD = 'EBD'
    CATEGORIA_CONFERENCIA = 'CONFERENCIA'
    CATEGORIA_RETIRO = 'RETIRO'
    CATEGORIA_JUVENTUDE = 'JUVENTUDE'
    CATEGORIA_HOMENS = 'HOMENS'
    CATEGORIA_MULHERES = 'MULHERES'
    CATEGORIA_MINISTERIO = 'MINISTERIO'
    CATEGORIA_ESPECIAL = 'ESPECIAL'
    CATEGORIA_OUTRO = 'OUTRO'

    CATEGORIA_CHOICES = [
        (CATEGORIA_CULTO, 'Culto'),
        (CATEGORIA_REUNIAO, 'Reunião'),
        (CATEGORIA_EBD, 'EBD'),
        (CATEGORIA_CONFERENCIA, 'Conferência'),
        (CATEGORIA_RETIRO, 'Retiro'),
        (CATEGORIA_JUVENTUDE, 'Juventude'),
        (CATEGORIA_HOMENS, 'Homens'),
        (CATEGORIA_MULHERES, 'Mulheres'),
        (CATEGORIA_MINISTERIO, 'Ministério'),
        (CATEGORIA_ESPECIAL, 'Evento Especial'),
        (CATEGORIA_OUTRO, 'Outro'),
    ]

    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    data = models.DateField()
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fim = models.TimeField(blank=True, null=True)
    local = models.CharField(max_length=150, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default=CATEGORIA_OUTRO)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ('data', 'hora_inicio', 'titulo')
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return self.titulo
