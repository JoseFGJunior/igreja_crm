from datetime import date
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect,render
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from apps.core.views import home_view
from apps.eventos.models import Evento
from apps.membros.models import Membro
from apps.mobile.models import PedidoOracao
from apps.mobile.pix import pix_payload
from .models import *
def registrar_pedido_oracao(request, config):
 if request.method != 'POST' or request.POST.get('formulario') != 'pedido_oracao': return {}
 nome=request.POST.get('nome','').strip(); telefone=request.POST.get('telefone','').strip(); pedido=request.POST.get('pedido','').strip()
 dados={'oracao_nome':nome,'oracao_telefone':telefone,'oracao_pedido':pedido}
 erros=[]
 if not telefone: erros.append('Informe seu telefone para que possamos entrar em contato.')
 if not pedido: erros.append('Escreva o seu pedido de oração.')
 if erros: dados['oracao_erros']=erros; return dados
 PedidoOracao.objects.create(igreja=config.igreja,nome=nome,telefone=telefone,pedido=pedido)
 dados['oracao_sucesso']='Seu pedido de oração foi recebido com carinho. Estamos orando por você.'
 dados.update({'oracao_nome':'','oracao_telefone':'','oracao_pedido':''})
 return dados


def ctx(c, request):
 h=date.today(); period=Q(data_inicio__isnull=True)|Q(data_inicio__lte=h); end=Q(data_fim__isnull=True)|Q(data_fim__gte=h)
 pix_code=pix_payload(c.pix_chave,c.nome_publico,c.cidade) if c.pix_chave else ''
 pix_qr_url=request.build_absolute_uri('/api/mobile/v1/pix/qr-code/?tenant='+c.igreja.slug) if pix_code else ''
 return {'config':c,'igreja':c.igreja,'pix_copia_e_cola':pix_code,'pix_qr_code_url':pix_qr_url,'banners':BannerSiteIgreja.objects.filter(igreja=c.igreja,ativo=True).filter(period,end),'programacao':ProgramacaoIgreja.objects.filter(igreja=c.igreja,ativo=True,exibir_site=True),'eventos':Evento.objects.filter(igreja=c.igreja,data__gte=h,exibir_site=True)[:6],'avisos':AvisoIgreja.objects.filter(igreja=c.igreja,ativo=True,exibir_site=True).filter(period,end)[:6],'aniversariantes':Membro.objects.filter(igreja=c.igreja,status__in=('MEMBRO','CONGREGADO'),autoriza_exibir_aniversario_site=True,data_nascimento__month=h.month,data_nascimento__day=h.day).order_by('nome')}

def app_redirect_url(request, config):
 if config.destino_publico != ConfiguracaoSiteIgreja.DESTINO_APP or not config.url_app_web or request.GET.get('portal') == '1': return None
 parsed = urlparse(config.url_app_web)
 query = parse_qs(parsed.query)
 query.setdefault('tenant', [config.igreja.slug])
 target = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
 current = urlparse(request.build_absolute_uri())
 target_parts = urlparse(target)
 if target_parts.netloc.lower() == current.netloc.lower() and target_parts.path.rstrip('/') == current.path.rstrip('/'):
  fallback = urlparse(request.build_absolute_uri('/app/'))
  target = urlunparse(fallback._replace(query=urlencode(query, doseq=True)))
 return target
def portal_domain_home(request):
 host=request.get_host().split(':')[0].lower().removeprefix('www.'); c=ConfiguracaoSiteIgreja.objects.select_related('igreja').filter(dominio_personalizado__iexact=host,site_ativo=True,igreja__ativa=True).first()
 if not c: return home_view(request)
 target=app_redirect_url(request,c)
 if target: return redirect(target)
 data=ctx(c,request); data.update(registrar_pedido_oracao(request,c)); return render(request,'portal/home.html',data)
def portal(request,slug):
 c=ConfiguracaoSiteIgreja.objects.select_related('igreja').filter(Q(slug_publico__iexact=slug)|Q(slug_publico__isnull=True,igreja__slug__iexact=slug)|Q(slug_publico='',igreja__slug__iexact=slug),site_ativo=True,igreja__ativa=True).first()
 if not c: raise Http404('Portal não encontrado')
 target=app_redirect_url(request,c)
 if target: return redirect(target)
 data=ctx(c,request); data.update(registrar_pedido_oracao(request,c)); return render(request,'portal/home.html',data)
