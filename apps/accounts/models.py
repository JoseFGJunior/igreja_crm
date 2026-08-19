from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.igrejas.models import Igreja


class Usuario(AbstractUser):
    pass



class UsuarioIgreja(models.Model):

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='igrejas'
    )

    igreja = models.ForeignKey(
        Igreja,
        on_delete=models.CASCADE,
        related_name='usuarios'
    )

    igreja_default = models.BooleanField(
        default=False
    )

    ativo = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('usuario', 'igreja')

    def __str__(self):
        return f'{self.usuario.username} - {self.igreja.nome}'