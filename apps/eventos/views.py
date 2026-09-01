from datetime import datetime, time
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import UsuarioIgreja
from apps.eventos.forms import EventoForm
from apps.eventos.models import Evento
from apps.core.views import build_xlsx


def get_igreja_selecionada(request):
    igreja_id = request.session.get('igreja_id')
    if not igreja_id:
        return None
    relacao = UsuarioIgreja.objects.select_related('igreja').filter(
        usuario=request.user, igreja_id=igreja_id, ativo=True, igreja__ativa=True
    ).first()
    return relacao.igreja if relacao else None


def evento_queryset(igreja):
    return Evento.objects.filter(igreja=igreja)


@login_required
def calendario_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    eventos = evento_queryset(igreja)
    filtro_valido = False
    try:
        inicio = date.fromisoformat(data_inicio) if data_inicio else None
        fim = date.fromisoformat(data_fim) if data_fim else None
        if inicio and fim and inicio <= fim:
            eventos = eventos.filter(data__range=(inicio, fim))
            filtro_valido = True
        elif data_inicio or data_fim:
            eventos = eventos.none()
    except ValueError:
        inicio = fim = None
        eventos = eventos.none()
    if not data_inicio and not data_fim:
        eventos = eventos.filter(data__gte=timezone.localdate())
    proximos_eventos = eventos.order_by('data', 'hora_inicio', 'titulo')
    if not filtro_valido:
        proximos_eventos = proximos_eventos[:10]
    return render(request, 'eventos/calendario.html', {
        'igreja': igreja,
        'proximos_eventos': proximos_eventos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'filtro_valido': filtro_valido,
    })


@login_required

@login_required
def eventos_exportar_excel_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    try:
        inicio = date.fromisoformat(data_inicio)
        fim = date.fromisoformat(data_fim)
    except (TypeError, ValueError):
        return redirect('eventos_calendario')
    if inicio > fim:
        return redirect('eventos_calendario')
    eventos = evento_queryset(igreja).filter(data__range=(inicio, fim)).order_by('data', 'hora_inicio', 'titulo')
    rows = [
        [f'Eventos - {igreja.nome}'],
        ['Título', 'Descrição', 'Data', 'Hora início', 'Hora fim', 'Local', 'Categoria', 'Observações'],
    ]
    for evento in eventos:
        rows.append([
            evento.titulo, evento.descricao, evento.data.strftime('%d/%m/%Y'),
            evento.hora_inicio.strftime('%H:%M') if evento.hora_inicio else '',
            evento.hora_fim.strftime('%H:%M') if evento.hora_fim else '',
            evento.local, evento.get_categoria_display(), evento.observacoes,
        ])
    response = HttpResponse(
        build_xlsx(rows, sheet_name='Eventos').getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="eventos-{inicio:%Y%m%d}-{fim:%Y%m%d}.xlsx"'
    return response
def calendario_json_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return JsonResponse([], safe=False)
    eventos = evento_queryset(igreja)
    inicio = request.GET.get('start')
    fim = request.GET.get('end')
    if inicio:
        try:
            eventos = eventos.filter(data__gte=datetime.fromisoformat(inicio.replace('Z', '+00:00')).date())
        except ValueError:
            pass
    if fim:
        try:
            eventos = eventos.filter(data__lt=datetime.fromisoformat(fim.replace('Z', '+00:00')).date())
        except ValueError:
            pass
    resultado = []
    for evento in eventos:
        inicio_evento = datetime.combine(evento.data, evento.hora_inicio or time.min)
        fim_evento = datetime.combine(evento.data, evento.hora_fim) if evento.hora_fim else None
        resultado.append({
            'id': evento.pk,
            'title': evento.titulo,
            'start': timezone.make_aware(inicio_evento).isoformat(),
            **({'end': timezone.make_aware(fim_evento).isoformat()} if fim_evento else {}),
            'url': f'/eventos/{evento.pk}/',
        })
    return JsonResponse(resultado, safe=False)


@login_required
def evento_create_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    data_inicial = request.GET.get('data', '')
    try:
        data_inicial = date.fromisoformat(data_inicial) if data_inicial else None
    except ValueError:
        data_inicial = None
    form = EventoForm(request.POST or None, initial={'data': data_inicial})
    if request.method == 'POST' and form.is_valid():
        evento = form.save(commit=False)
        evento.igreja = igreja
        evento.save()
        return redirect('eventos_calendario')
    return render(request, 'eventos/form.html', {'form': form, 'igreja': igreja, 'titulo': 'Novo evento'})


@login_required
def evento_detail_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    evento = get_object_or_404(evento_queryset(igreja), pk=pk)
    return render(request, 'eventos/detalhe.html', {'evento': evento, 'igreja': igreja})


@login_required
def evento_update_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    evento = get_object_or_404(evento_queryset(igreja), pk=pk)
    form = EventoForm(request.POST or None, instance=evento)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('evento_detail', pk=evento.pk)
    return render(request, 'eventos/form.html', {'form': form, 'evento': evento, 'igreja': igreja, 'titulo': 'Editar evento'})


@login_required
def evento_delete_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    evento = get_object_or_404(evento_queryset(igreja), pk=pk)
    if request.method == 'POST':
        evento.delete()
        return redirect('eventos_calendario')
    return render(request, 'eventos/confirmar_exclusao.html', {'evento': evento, 'igreja': igreja})
