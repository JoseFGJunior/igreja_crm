from django.db import models


class Igreja(models.Model):

    PLANO_GRATUITO = 'GRATUITO'
    PLANO_COMPLETO = 'COMPLETO'

    PLANO_CHOICES = [
        (PLANO_GRATUITO, 'Gratuito'),
        (PLANO_COMPLETO, 'Completo'),
    ]

    nome = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        unique=True
    )

    ativa = models.BooleanField(
        default=True
    )

    plano = models.CharField(
        max_length=20,
        choices=PLANO_CHOICES,
        default=PLANO_GRATUITO
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nome

    @property
    def plano_completo_ativo(self):
        return self.ativa and self.plano == self.PLANO_COMPLETO
