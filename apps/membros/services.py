from datetime import timedelta

from django.db import transaction

from apps.membros.models import AcompanhamentoVisitante, MensagemWhatsAppVisitante, Membro, VisitaVisitante


JORNADA_PADRAO = (
    ('24H', 1),
    ('7D', 7),
    ('15D', 15),
)

MENSAGENS_WHATSAPP_PADRAO = {
    '24H': 'Olá! 😊 Foi uma alegria receber você em nossa igreja!\nEsperamos que tenha se sentido bem e acolhido. Queremos lembrar que Deus conhece você e cuida de cada detalhe da sua vida.\n📖 “Lancem sobre ele toda a sua ansiedade, porque ele tem cuidado de vocês.” — 1 Pedro 5:7\nQue Deus abençoe sua semana! 🙏',
    '7D': 'Olá! Passamos para saber como você está. 😊\nNunca se esqueça: mesmo nos dias difíceis, Deus está perto e continua cuidando de você.\n📖 “Não temas, porque eu sou contigo; não te assombres, porque eu sou teu Deus.” — Isaías 41:10\nConte conosco. Estamos orando por você! 🙏',
    '15D': 'Olá! 😊 Queremos dizer que foi muito bom ter você conosco e que será uma alegria receber você novamente.\nDeus deseja caminhar conosco e nos conduzir em cada etapa da vida.\n📖 “O Senhor é o meu pastor; nada me faltará.” — Salmo 23:1\nVocê é sempre bem-vindo! Esperamos ver você novamente. ❤️🙏',
}


def normalizar_whatsapp(numero):
    numero = ''.join(
        caractere
        for caractere in (numero or '')
        if caractere.isdigit()
    )

    if numero.startswith('00'):
        numero = numero[2:]

    if numero.startswith('0') and len(numero) in (11, 12):
        numero = numero[1:]

    if not numero.startswith('55') and len(numero) in (10, 11):
        numero = f'55{numero}'

    return numero


def garantir_mensagens_whatsapp(igreja):
    mensagens = {}
    for tipo, texto in MENSAGENS_WHATSAPP_PADRAO.items():
        mensagem, _ = MensagemWhatsAppVisitante.objects.get_or_create(
            igreja=igreja,
            tipo=tipo,
            defaults={'mensagem': texto},
        )
        mensagens[tipo] = mensagem
    return mensagens


@transaction.atomic
def criar_jornada_visitante(visitante):
    for tipo, dias in JORNADA_PADRAO:
        AcompanhamentoVisitante.objects.get_or_create(
            igreja=visitante.igreja,
            visitante=visitante,
            tipo=tipo,
            defaults={
                'data_prevista': visitante.data_primeira_visita + timedelta(days=dias),
                'responsavel': visitante.responsavel_visitante,
            },
        )


@transaction.atomic
def registrar_primeira_visita(visitante):
    VisitaVisitante.objects.get_or_create(
        igreja=visitante.igreja,
        visitante=visitante,
        data_visita=visitante.data_primeira_visita,
    )
