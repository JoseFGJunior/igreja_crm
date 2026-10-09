from functools import wraps
import json
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Count

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from apps.eventos.models import Evento
from apps.portal.models import AvisoIgreja, ConfiguracaoSiteIgreja

from apps.accounts.models import UsuarioIgreja
from .models import AcessoApp, ConfiguracaoApp, MensagemApp, PalavraDoDia, PedidoOracao, PushSubscription
from .pix import pix_payload
PUBLIC_STATUSES = (PalavraDoDia.STATUS_APROVADO, PalavraDoDia.STATUS_PUBLICADO)

def get_igreja_selecionada(request):
    igreja_id = request.session.get('igreja_id')
    if not igreja_id:
        return None
    relacao = UsuarioIgreja.objects.select_related('igreja').filter(
        usuario=request.user,
        igreja_id=igreja_id,
        ativo=True,
        igreja__ativa=True,
    ).first()
    return relacao.igreja if relacao else None


@login_required
@permission_required('mobile.view_mensagemapp', raise_exception=True)
def mensagem_dashboard_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    hoje = timezone.localdate()
    mensagens = MensagemApp.objects.filter(igreja=igreja)
    return render(request, 'mobile/mensagem_dashboard.html', {
        'igreja': igreja,
        'mensagens': mensagens.order_by('-data', 'ordem', '-created_at'),
        'total_mensagens': mensagens.count(),
        'mensagens_ativas': mensagens.filter(ativo=True).count(),
        'mensagens_publicadas': mensagens.filter(ativo=True, data__lte=hoje).count(),
        'proximas_mensagens': mensagens.filter(ativo=True, data__gt=hoje).count(),
    })

@login_required
@permission_required('mobile.view_acessoapp', raise_exception=True)
def acesso_dashboard_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    hoje = timezone.localdate()
    acessos = AcessoApp.objects.filter(igreja=igreja)
    eventos = acessos.values('evento').annotate(total=Count('id')).order_by('-total', 'evento')[:10]
    return render(request, 'mobile/acessos_dashboard.html', {
        'igreja': igreja,
        'acessos': acessos.select_related('usuario').order_by('-acessado_em', '-id')[:100],
        'eventos': eventos,
        'total_acessos': acessos.count(),
        'visitantes_unicos': acessos.values('visitante_id').distinct().count(),
        'acessos_hoje': acessos.filter(acessado_em__date=hoje).count(),
        'eventos_distintos': acessos.values('evento').distinct().count(),
    })


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

def _configuracao_ativa(tenant=None):
    queryset = ConfiguracaoApp.objects.select_related('igreja').filter(ativo=True, igreja__ativa=True)
    tenant = str(tenant or '').strip()
    return queryset.filter(igreja__slug__iexact=tenant).first() if tenant else queryset.first()

@cors_api
@csrf_exempt
def registrar_acesso(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método não permitido.'}, status=405)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)
    config = _configuracao_ativa(payload.get('tenant'))
    visitante_id = str(payload.get('visitante_id') or '').strip()
    evento = str(payload.get('evento') or '').strip()
    recurso = str(payload.get('recurso') or '').strip()
    if not config:
        return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    if not visitante_id or not evento:
        return JsonResponse({'detail': 'visitante_id e evento são obrigatórios.'}, status=400)
    if len(visitante_id) > 100 or len(evento) > 80 or len(recurso) > 120:
        return JsonResponse({'detail': 'Dados do evento excedem o limite permitido.'}, status=400)
    dados = payload.get('dados') if isinstance(payload.get('dados'), dict) else {}
    AcessoApp.objects.create(igreja=config.igreja, visitante_id=visitante_id, canal=AcessoApp.CANAL_APP, evento=evento, recurso=recurso, dispositivo=str(payload.get('dispositivo') or '')[:40], user_agent=request.headers.get('User-Agent', ''), dados=dados)
    return JsonResponse({'detail': 'Acesso registrado.'}, status=201)
def _palavra_data(request, palavra):
    return {'id': palavra.id, 'igreja_id': palavra.igreja_id, 'data': palavra.data.isoformat(), 'titulo': palavra.titulo, 'referencia_biblica': palavra.referencia_biblica, 'texto_biblico': palavra.texto_biblico, 'reflexao': palavra.reflexao, 'aplicacao': palavra.aplicacao, 'oracao': palavra.oracao, 'imagem': _media_url(request, palavra.imagem)}

def _igreja_data(request, config):
    igreja = config.igreja
    portal_config = ConfiguracaoSiteIgreja.objects.filter(igreja=igreja, site_ativo=True).first()
    pix_key = portal_config.pix_chave if portal_config else ''
    pix_code = pix_payload(pix_key, portal_config.nome_publico if portal_config else igreja.nome, portal_config.cidade if portal_config else '')
    return {'id': igreja.id, 'nome': igreja.nome, 'slug': igreja.slug, 'nome_app': config.nome_app, 'nome_exibicao': config.nome_exibicao or igreja.nome, 'descricao': config.descricao, 'logo': _media_url(request, config.logo), 'banner_principal': _media_url(request, config.banner_principal), 'mensagem_boas_vindas': config.mensagem_boas_vindas, 'telefone': config.telefone, 'whatsapp': config.whatsapp, 'instagram': config.instagram, 'youtube': config.youtube, 'endereco': config.endereco, 'bairro': config.bairro, 'cidade': config.cidade, 'uf': config.uf, 'cep': config.cep, 'latitude': config.latitude, 'longitude': config.longitude, 'horarios_cultos': config.horarios_cultos, 'pix_chave': pix_key, 'pix_copia_e_cola': pix_code, 'pix_qr_code': request.build_absolute_uri('/api/mobile/v1/pix/qr-code/?tenant='+igreja.slug) if pix_code else None}

@cors_api
def palavra_do_dia(request):
    config = _configuracao_ativa(request.GET.get('tenant'))
    if not config: return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    palavra = PalavraDoDia.objects.filter(igreja=config.igreja, data__lte=timezone.localdate(), status__in=PUBLIC_STATUSES, publicado=True).first()
    if not palavra: return JsonResponse({'detail': 'Palavra do dia não disponível.'}, status=404)
    return JsonResponse(_palavra_data(request, palavra))

def _evento_data(request, evento):
    return {'id': evento.id, 'titulo': evento.titulo, 'descricao': evento.descricao, 'data': evento.data.isoformat(), 'hora_inicio': evento.hora_inicio.isoformat() if evento.hora_inicio else None, 'hora_fim': evento.hora_fim.isoformat() if evento.hora_fim else None, 'local': evento.local, 'categoria': evento.categoria, 'imagem': _media_url(request, evento.imagem)}

def _mensagem_data(request, mensagem):
    return {'id': mensagem.id, 'data': mensagem.data.isoformat(), 'titulo': mensagem.titulo, 'descricao': mensagem.descricao, 'youtube_url': mensagem.youtube_url, 'imagem': _media_url(request, mensagem.imagem)}
def _aviso_data(request, aviso):
    return {'id': aviso.id, 'titulo': aviso.titulo, 'descricao': aviso.descricao, 'imagem': _media_url(request, aviso.imagem), 'destaque': aviso.destaque}

@cors_api
def home(request):
    config = _configuracao_ativa(request.GET.get('tenant'))
    if not config: return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    hoje = timezone.localdate()
    palavra = PalavraDoDia.objects.filter(igreja=config.igreja, data__lte=hoje, status__in=PUBLIC_STATUSES, publicado=True).first()
    eventos = Evento.objects.filter(igreja=config.igreja, data__gte=hoje, exibir_site=True).order_by('data', 'hora_inicio', 'titulo')[:10]
    avisos = AvisoIgreja.objects.filter(igreja=config.igreja, ativo=True, exibir_site=True)[:10]
    mensagens = MensagemApp.objects.filter(igreja=config.igreja, ativo=True)
    mensagem_dia = mensagens.filter(data=hoje).order_by('ordem', '-created_at').first()
    return JsonResponse({'igreja': _igreja_data(request, config), 'palavra_dia': _palavra_data(request, palavra) if palavra else None, 'mensagem_dia': _mensagem_data(request, mensagem_dia) if mensagem_dia else None, 'reconstruir': [], 'estudos_destaque': [], 'proximos_eventos': [_evento_data(request, x) for x in eventos], 'avisos': [_aviso_data(request, x) for x in avisos], 'mensagens': [_mensagem_data(request, x) for x in mensagens]})

def prototipo(request):
    config = _configuracao_ativa(request.GET.get('tenant'))
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
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)
    config = _configuracao_ativa(payload.get('tenant'))
    if not config:
        return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    nome = str(payload.get('nome', '')).strip()
    telefone = str(payload.get('telefone', '')).strip()
    pedido = str(payload.get('pedido', '')).strip()
    if not telefone or not pedido:
        return JsonResponse({'detail': 'Telefone e pedido são obrigatórios.'}, status=400)
    item = PedidoOracao.objects.create(igreja=config.igreja, nome=nome, telefone=telefone, pedido=pedido)
    return JsonResponse({'id': item.id, 'detail': 'Pedido de oração enviado com sucesso.'}, status=201)
@cors_api
def push_public_key(request):
    if request.method != 'GET':
        return JsonResponse({'detail': 'Método não permitido.'}, status=405)
    public_key = getattr(settings, 'PUSH_VAPID_PUBLIC_KEY', '')
    if not public_key:
        return JsonResponse({'detail': 'Notificações push ainda não configuradas.'}, status=503)
    return JsonResponse({'publicKey': public_key})


def _push_config_from_payload(payload):
    tenant = str(payload.get('tenant') or '').strip()
    queryset = ConfiguracaoApp.objects.select_related('igreja').filter(ativo=True, igreja__ativa=True)
    return queryset.filter(igreja__slug__iexact=tenant).first() if tenant else queryset.first()


@cors_api
@csrf_exempt
def push_subscribe(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método não permitido.'}, status=405)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)
    config = _push_config_from_payload(payload)
    subscription = payload.get('subscription') or {}
    keys = subscription.get('keys') or {}
    endpoint = str(subscription.get('endpoint') or '').strip()
    p256dh = str(keys.get('p256dh') or '').strip()
    auth = str(keys.get('auth') or '').strip()
    if not config:
        return JsonResponse({'detail': 'Igreja não encontrada.'}, status=404)
    if not endpoint or not p256dh or not auth:
        return JsonResponse({'detail': 'Inscrição de push incompleta.'}, status=400)
    item, _ = PushSubscription.objects.update_or_create(endpoint=endpoint, defaults={
        'igreja': config.igreja, 'p256dh': p256dh, 'auth': auth,
        'user_agent': request.headers.get('User-Agent', ''), 'ativo': True,
    })
    return JsonResponse({'id': item.id, 'detail': 'Notificações ativadas.'}, status=201)


@cors_api
@csrf_exempt
def push_unsubscribe(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método não permitido.'}, status=405)
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)
    endpoint = str(payload.get('endpoint') or '').strip()
    if endpoint:
        PushSubscription.objects.filter(endpoint=endpoint).update(ativo=False)
    return JsonResponse({'detail': 'Notificações desativadas.'})
@cors_api
def eventos(request):
    tenant = (request.GET.get('tenant') or '').strip()
    queryset = ConfiguracaoApp.objects.select_related('igreja').filter(ativo=True, igreja__ativa=True)
    config = queryset.filter(igreja__slug__iexact=tenant).first() if tenant else queryset.first()
    if not config:
        return JsonResponse({'detail': 'Nenhuma igreja habilitada para o aplicativo.'}, status=404)
    hoje = timezone.localdate()
    itens = Evento.objects.filter(igreja=config.igreja, data__gte=hoje, exibir_site=True).order_by('data', 'hora_inicio', 'titulo')
    return JsonResponse({'eventos': [_evento_data(request, item) for item in itens]})
@cors_api
def pix_qr_code(request):
    tenant = (request.GET.get('tenant') or '').strip()
    config = ConfiguracaoSiteIgreja.objects.select_related('igreja').filter(igreja__slug__iexact=tenant, site_ativo=True).first() if tenant else ConfiguracaoSiteIgreja.objects.filter(site_ativo=True).first()
    if not config or not config.pix_chave:
        return JsonResponse({'detail': 'Chave PIX não configurada.'}, status=404)
    import qrcode
    code = pix_payload(config.pix_chave, config.nome_publico, config.cidade)
    image = qrcode.make(code)
    buffer = __import__('io').BytesIO()
    image.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')