from django.db import models
from urllib.parse import parse_qs
from urllib.parse import urlparse


class TenantModel(models.Model):

    igreja = models.ForeignKey(
        'igrejas.Igreja',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract = True


class MensagemAniversario(TenantModel):

    texto = models.TextField(
        default='Olá, {nome}! 🎉\n\nDesejamos a você um feliz aniversário! Que Deus abençoe sua vida e sua caminhada. 🙏'
    )

    versiculo = models.TextField(
        blank=True,
        default='“O Senhor te abençoe e te guarde.” — Números 6:24'
    )

    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Mensagem de aniversário'
        verbose_name_plural = 'Mensagens de aniversário'
        constraints = [
            models.UniqueConstraint(
                fields=('igreja',),
                name='unique_mensagem_aniversario_igreja'
            )
        ]


class AcaoMissionaria(models.Model):

    titulo = models.CharField(
        max_length=150
    )

    descricao = models.TextField()

    imagem = models.FileField(
        upload_to='acoes_missionarias/'
    )

    youtube_url = models.URLField(
        blank=True,
        null=True
    )

    data_acao = models.DateField(
        blank=True,
        null=True
    )

    local = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    destaque = models.BooleanField(
        default=False
    )

    ativo = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Acao missionaria'
        verbose_name_plural = 'Acoes missionarias'
        ordering = (
            '-destaque',
            '-data_acao',
            '-created_at',
        )

    def __str__(self):
        return self.titulo

    @property
    def youtube_embed_url(self):
        if not self.youtube_url:
            return ''

        parsed_url = urlparse(
            self.youtube_url.strip()
        )
        host = parsed_url.netloc.lower()
        path = parsed_url.path.strip('/')
        video_id = ''

        if 'youtu.be' in host:
            video_id = path.split('/')[0]
        elif 'youtube.com' in host:
            if path == 'watch':
                video_id = parse_qs(
                    parsed_url.query
                ).get(
                    'v',
                    ['']
                )[0]
            elif path.startswith('embed/'):
                video_id = path.split('/')[1]
            elif path.startswith('shorts/'):
                video_id = path.split('/')[1]

        if not video_id:
            return ''

        return f'https://www.youtube.com/embed/{video_id}'
