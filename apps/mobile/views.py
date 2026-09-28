from functools import wraps
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from apps.eventos.models import Evento
from apps.portal.models import AvisoIgreja
from .models import ConfiguracaoApp, PalavraDoDia, PedidoOracao
PUBLIC_STATUSES = (PalavraDoDia.STATUS_APROVADO, PalavraDoDia.STATUS_PUBLICADO)

def cors_api(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method == 'OPTIONS':
            response = JsonResponse({}, status=204)
        else:
            response = view(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Private-Network'] = 'true'
        return response
    return wrapped

def _media_url(request, field):
    return request.build_absolute_uri(field.url) if field else None

def _configuracao_ativa():
    return ConfiguracaoApp.objects.select_related('igreja').filter(ativo=True, igreja__ativa=True).first()

def _palavra_data(request, palavra):
    return {'id': palavra.id, 'igreja_id': palavra.igreja_id, 'data': palavra.data.isoformat(), 'titulo': palavra.titulo, 'referencia_biblica': palavra.referencia_biblica, 'texto_biblico': palavra.texto_biblico, 'reflexao': palavra.reflexao, 'aplicacao': palavra.aplicacao, 'oracao': palavra.oracao, 'imagem': _media_url(request, palavra.imagem)}

def _igreja_data(request, config):
    igreja = config.igreja
    return {'id': igreja.id, 'nome': igreja.nome, 'slug': igreja.slug, 'nome_app': config.nome_app, 'nome_exibicao': config.nome_exibicao or igreja.nome, 'descricao': config.descricao, 'logo': _media_url(request, config.logo), 'banner_principal': _media_url(request, config.banner_principal), 'mensagem_boas_vindas': config.mensagem_boas_vindas, 'telefone': config.telefone, 'whatsapp': config.whatsapp, 'instagram': config.instagram, 'youtube': config.youtube, 'endereco': config.endereco, 'bairro': config.bairro, 'cidade': config.cidade, 'uf': config.uf, 'cep': config.cep, 'latitude': config.latitude, 'longitude': config.longitude, 'horarios_cultos': config.horarios_cultos}

@cors_api
def palavra_do_dia(request):
    config = _configuracao_ativa()
    if not config: return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    palavra = PalavraDoDia.objects.filter(igreja=config.igreja, data__lte=timezone.localdate(), status__in=PUBLIC_STATUSES, publicado=True).first()
    if not palavra: return JsonResponse({'detail': 'Palavra do dia não disponível.'}, status=404)
    return JsonResponse(_palavra_data(request, palavra))

def _evento_data(request, evento):
    return {'id': evento.id, 'titulo': evento.titulo, 'descricao': evento.descricao, 'data': evento.data.isoformat(), 'hora_inicio': evento.hora_inicio.isoformat() if evento.hora_inicio else None, 'hora_fim': evento.hora_fim.isoformat() if evento.hora_fim else None, 'local': evento.local, 'categoria': evento.categoria, 'imagem': _media_url(request, evento.imagem)}

def _aviso_data(request, aviso):
    return {'id': aviso.id, 'titulo': aviso.titulo, 'descricao': aviso.descricao, 'imagem': _media_url(request, aviso.imagem), 'destaque': aviso.destaque}

@cors_api
def home(request):
    config = _configuracao_ativa()
    if not config: return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    hoje = timezone.localdate()
    palavra = PalavraDoDia.objects.filter(igreja=config.igreja, data__lte=hoje, status__in=PUBLIC_STATUSES, publicado=True).first()
    eventos = Evento.objects.filter(igreja=config.igreja, data__gte=hoje, exibir_site=True)[:10]
    avisos = AvisoIgreja.objects.filter(igreja=config.igreja, ativo=True, exibir_site=True)[:10]
    return JsonResponse({'igreja': _igreja_data(request, config), 'palavra_dia': _palavra_data(request, palavra) if palavra else None, 'reconstruir': [], 'estudos_destaque': [], 'proximos_eventos': [_evento_data(request, x) for x in eventos], 'avisos': [_aviso_data(request, x) for x in avisos]})

def prototipo(request):
    config = _configuracao_ativa()
    hoje = timezone.localdate()
    if config:
        palavra = PalavraDoDia.objects.filter(igreja=config.igreja, data__lte=hoje, status__in=PUBLIC_STATUSES, publicado=True).first()
        eventos = list(Evento.objects.filter(igreja=config.igreja, data__gte=hoje, exibir_site=True)[:6])
        avisos = list(AvisoIgreja.objects.filter(igreja=config.igreja, ativo=True, exibir_site=True)[:4])
        igreja = _igreja_data(request, config)
    else:
        palavra = None; eventos = []; avisos = []
        igreja = {'nome_exibicao': 'PIB Cruz', 'nome': 'Primeira Igreja Batista em Cruz de Rebouças', 'descricao': 'Uma igreja que ama a Deus, ama pessoas e vive para fazer a diferença.', 'cidade': 'Igarassu', 'uf': 'PE', 'horarios_cultos': 'Domingo · 09h e 18h\nQuarta-feira · 19h30', 'instagram': '', 'youtube': '', 'whatsapp': '', 'endereco': '', 'logo': None, 'banner_principal': None}
    return render(request, 'mobile/prototipo.html', {'igreja': igreja, 'palavra': _palavra_data(request, palavra) if palavra else None, 'eventos': [_evento_data(request, item) for item in eventos], 'avisos': [_aviso_data(request, item) for item in avisos]})
@cors_api
@csrf_exempt
def pedidos_oracao(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método não permitido.'}, status=405)
    config = _configuracao_ativa()
    if not config:
        return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)
    nome = str(payload.get('nome', '')).strip()
    telefone = str(payload.get('telefone', '')).strip()
    pedido = str(payload.get('pedido', '')).strip()
    if not telefone or not pedido:
        return JsonResponse({'detail': 'Telefone e pedido são obrigatórios.'}, status=400)
    item = PedidoOracao.objects.create(igreja=config.igreja, nome=nome, telefone=telefone, pedido=pedido)
    return JsonResponse({'id': item.id, 'detail': 'Pedido de oração enviado com sucesso.'}, status=201)