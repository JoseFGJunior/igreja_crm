from datetime import date
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect,render
from apps.core.views import home_view
from apps.eventos.models import Evento
from .models import *
def ctx(c):
 h=date.today(); period=Q(data_inicio__isnull=True)|Q(data_inicio__lte=h); end=Q(data_fim__isnull=True)|Q(data_fim__gte=h)
 return {'config':c,'igreja':c.igreja,'banners':BannerSiteIgreja.objects.filter(igreja=c.igreja,ativo=True).filter(period,end),'programacao':ProgramacaoIgreja.objects.filter(igreja=c.igreja,ativo=True,exibir_site=True),'eventos':Evento.objects.filter(igreja=c.igreja,data__gte=h,exibir_site=True)[:6],'avisos':AvisoIgreja.objects.filter(igreja=c.igreja,ativo=True,exibir_site=True).filter(period,end)[:6]}
def portal_domain_home(request):
 host=request.get_host().split(':')[0].lower().removeprefix('www.'); c=ConfiguracaoSiteIgreja.objects.select_related('igreja').filter(dominio_personalizado__iexact=host,site_ativo=True,igreja__ativa=True).first()
 return render(request,'portal/home.html',ctx(c)) if c else home_view(request)
def portal(request,slug):
 c=ConfiguracaoSiteIgreja.objects.select_related('igreja').filter(Q(slug_publico__iexact=slug)|Q(slug_publico__isnull=True,igreja__slug__iexact=slug)|Q(slug_publico='',igreja__slug__iexact=slug),site_ativo=True,igreja__ativa=True).first()
 if not c: raise Http404('Portal não encontrado')
 return render(request,'portal/home.html',ctx(c))