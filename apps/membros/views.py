from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import UsuarioIgreja
from apps.membros.forms import MembroForm
from apps.membros.forms import MensagemWhatsAppVisitanteForm
from apps.membros.forms import VisitanteForm
from apps.membros.models import AcompanhamentoVisitante
from apps.membros.models import MensagemWhatsAppVisitante
from apps.membros.models import Membro
from apps.membros.models import VisitaVisitante
from apps.core.models import MensagemAniversario
from apps.membros.services import criar_jornada_visitante
from apps.membros.services import normalizar_whatsapp
from apps.membros.services import garantir_mensagens_whatsapp
from apps.membros.services import registrar_primeira_visita
from urllib.parse import quote



def preparar_url_aniversario(membro, igreja, mensagem):
    telefone = membro.telefone or membro.whatsapp
    if not telefone or not mensagem or not mensagem.ativa:
        return None
    primeiro_nome = membro.nome.split()[0] if membro.nome else ''
    texto = mensagem.texto.replace('{nome}', primeiro_nome)
    if mensagem.versiculo:
        texto = f'{texto}\n\n📖 {mensagem.versiculo}'
    texto = f'{texto}\n\n{igreja.nome}'
    return f'https://wa.me/{normalizar_whatsapp(telefone)}?text={quote(texto)}'


def aniversariantes_dos_proximos_dias(membros, hoje, quantidade=7):
    datas = {((hoje + timedelta(days=offset)).month, (hoje + timedelta(days=offset)).day): offset for offset in range(quantidade)}
    aniversariantes = [membro for membro in membros if membro.data_nascimento and (membro.data_nascimento.month, membro.data_nascimento.day) in datas]
    return sorted(aniversariantes, key=lambda membro: (datas[(membro.data_nascimento.month, membro.data_nascimento.day)], membro.nome))

def get_igreja_selecionada(request):
    igreja_id = request.session.get('igreja_id')

    if not igreja_id:
        return None

    relacao = UsuarioIgreja.objects.select_related('igreja').filter(
        usuario=request.user,
        igreja_id=igreja_id,
        ativo=True,
        igreja__ativa=True
    ).first()

    if relacao:
        return relacao.igreja
    return None


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def membro_list_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    pesquisa = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    membros = Membro.objects.filter(
        igreja=igreja
    ).order_by(
        'nome'
    )

    if pesquisa:
        membros = membros.filter(
            nome__icontains=pesquisa
        )
    if status in dict(Membro.STATUS_CHOICES):
        membros = membros.filter(status=status)

    total_membros = membros.count()
    return render(
        request,
        'membros/membro_list.html',
        {
            'igreja': igreja,
            'membros': membros,
            'pesquisa': pesquisa,
            'status': status,
            'status_choices': Membro.STATUS_CHOICES,
            'total_membros': total_membros,
        }
    )


@login_required
@permission_required('membros.add_membro', raise_exception=True)
def membro_create_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    form = MembroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        membro = form.save(commit=False)
        membro.igreja = igreja
        membro.save()

        return redirect('membro_list')

    return render(
        request,
        'membros/membro_form.html',
        {
            'form': form,
            'igreja': igreja,
            'titulo': 'Novo membro',
        }
    )


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def membro_update_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    membro = get_object_or_404(
        Membro,
        pk=pk,
        igreja=igreja
    )

    form = MembroForm(
        request.POST or None,
        instance=membro
    )

    if request.method == 'POST' and form.is_valid():
        form.save()

        return redirect('membro_list')

    return render(
        request,
        'membros/membro_form.html',
        {
            'form': form,
            'igreja': igreja,
            'membro': membro,
            'titulo': 'Editar membro',
        }
    )


@login_required
@permission_required('membros.delete_membro', raise_exception=True)
def membro_delete_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    membro = get_object_or_404(
        Membro,
        pk=pk,
        igreja=igreja
    )

    if request.method == 'POST':
        membro.delete()

        return redirect('membro_list')

    return render(
        request,
        'membros/membro_confirm_delete.html',
        {
            'igreja': igreja,
            'membro': membro,
        }
    )


def visitante_queryset(igreja):
    return Membro.objects.filter(
        igreja=igreja,
        status='VISITANTE',
    ).select_related('responsavel_visitante')


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def visitante_dashboard_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')

    hoje = timezone.localdate()
    visitantes = visitante_queryset(igreja)
    acompanhamentos = AcompanhamentoVisitante.objects.filter(igreja=igreja)

    return render(request, 'membros/visitante_dashboard.html', {
        'igreja': igreja,
        'visitantes_mes': visitantes.filter(data_primeira_visita__year=hoje.year, data_primeira_visita__month=hoje.month).count(),
        'visitantes_semana': visitantes.filter(data_primeira_visita__gte=hoje - timedelta(days=hoje.weekday()), data_primeira_visita__lte=hoje).count(),
        'acompanhamentos_hoje': acompanhamentos.filter(status='PENDENTE', data_prevista=hoje).count(),
        'acompanhamentos_atrasados': acompanhamentos.filter(status='PENDENTE', data_prevista__lt=hoje).count(),
        'em_acompanhamento': visitantes.filter(status_visitante='ACOMPANHAMENTO').count(),
        'retornaram': visitantes.filter(status_visitante='RETORNOU').count(),
    })


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def visitante_list_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')

    visitantes = visitante_queryset(igreja)
    pesquisa = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    if pesquisa:
        visitantes = visitantes.filter(
            nome__icontains=pesquisa
        )
    if status:
        visitantes = visitantes.filter(status_visitante=status)

    return render(request, 'membros/visitante_list.html', {
        'igreja': igreja,
        'visitantes': visitantes.order_by('nome'),
        'pesquisa': pesquisa,
        'status': status,
        'status_choices': Membro.STATUS_VISITANTE_CHOICES,
    })


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def visitante_acompanhamentos_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    hoje = timezone.localdate()
    acompanhamentos = AcompanhamentoVisitante.objects.filter(
        igreja=igreja,
        status='PENDENTE',
    ).select_related('visitante', 'responsavel')
    membros = list(Membro.objects.filter(igreja=igreja).order_by('nome'))
    mensagem_aniversario, _ = MensagemAniversario.objects.get_or_create(igreja=igreja)
    aniversariantes = aniversariantes_dos_proximos_dias(membros, hoje)
    aniversariantes_hoje = []
    for membro in aniversariantes:
        membro.whatsapp_url = preparar_url_aniversario(membro, igreja, mensagem_aniversario)
        if membro.data_nascimento.month == hoje.month and membro.data_nascimento.day == hoje.day:
            aniversariantes_hoje.append(membro)

    return render(request, 'membros/visitante_acompanhamentos.html', {
        'igreja': igreja,
        'hoje': acompanhamentos.filter(data_prevista=hoje),
        'atrasados': acompanhamentos.filter(data_prevista__lt=hoje),
        'aniversariantes_hoje': aniversariantes_hoje,
        'proximos_aniversariantes': aniversariantes,
        'aniversariantes_hoje_count': len(aniversariantes_hoje),
    })

@login_required
@permission_required('membros.add_membro', raise_exception=True)
def visitante_create_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')

    form = VisitanteForm(
        request.POST or None,
        igreja=igreja,
        initial={'data_primeira_visita': timezone.localdate()},
    )
    if request.method == 'POST' and form.is_valid():
        visitante = form.save(commit=False)
        visitante.igreja = igreja
        visitante.whatsapp = normalizar_whatsapp(visitante.whatsapp)
        visitante.save()
        registrar_primeira_visita(visitante)
        criar_jornada_visitante(visitante)
        return redirect('visitante_detail', pk=visitante.pk)

    return render(request, 'membros/visitante_form.html', {
        'form': form,
        'igreja': igreja,
    })


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def visitante_update_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    visitante = get_object_or_404(visitante_queryset(igreja), pk=pk)
    form = VisitanteForm(request.POST or None, instance=visitante, igreja=igreja)
    if request.method == 'POST' and form.is_valid():
        visitante = form.save(commit=False)
        visitante.igreja = igreja
        visitante.whatsapp = normalizar_whatsapp(visitante.whatsapp)
        visitante.save()
        return redirect('visitante_detail', pk=visitante.pk)
    return render(request, 'membros/visitante_form.html', {
        'form': form,
        'igreja': igreja,
        'visitante': visitante,
    })


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def visitante_detail_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    visitante = get_object_or_404(visitante_queryset(igreja), pk=pk)
    acompanhamentos = visitante.acompanhamentos_visitante.filter(igreja=igreja)
    mensagens = garantir_mensagens_whatsapp(igreja)
    for acompanhamento in acompanhamentos:
        mensagem = mensagens.get(acompanhamento.tipo)
        if mensagem:
            texto = f'{mensagem.mensagem}\n\nIgreja: {igreja.nome}'
            acompanhamento.whatsapp_url = (
                f'https://wa.me/{normalizar_whatsapp(visitante.whatsapp)}'
                f'?text={quote(texto)}'
            )
    return render(request, 'membros/visitante_detail.html', {
        'igreja': igreja,
        'visitante': visitante,
        'visitas': visitante.visitas_visitante.filter(igreja=igreja),
        'acompanhamentos': acompanhamentos,
        'proximo_contato': acompanhamentos.filter(status='PENDENTE').first(),
        'whatsapp_url': f'https://wa.me/{normalizar_whatsapp(visitante.whatsapp)}',
        'resultado_choices': (
            'Contato realizado', 'Não respondeu', 'Número inválido',
            'Entrar em contato novamente', 'Demonstrou interesse',
            'Pretende retornar', 'Retornou à igreja', 'Não deseja mais contato',
        ),
    })


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def visitante_mensagens_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    mensagens = garantir_mensagens_whatsapp(igreja)
    if request.method == 'POST':
        for tipo, mensagem in mensagens.items():
            mensagem.mensagem = request.POST.get(f'mensagem_{tipo}', '').strip()
            mensagem.save(update_fields=['mensagem', 'updated_at'])
        return redirect('visitante_mensagens')
    return render(request, 'membros/visitante_mensagens.html', {
        'igreja': igreja,
        'mensagens': mensagens,
    })


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def visitante_contato_view(request, pk):
    igreja = get_igreja_selecionada(request)
    visitante = get_object_or_404(visitante_queryset(igreja), pk=pk)
    acompanhamento = get_object_or_404(
        AcompanhamentoVisitante,
        pk=request.POST.get('acompanhamento_id'),
        igreja=igreja,
        visitante=visitante,
    )
    acompanhamento.status = 'CONCLUIDO'
    acompanhamento.data_realizada = request.POST.get('data_realizada') or timezone.localdate()
    acompanhamento.resultado = request.POST.get('resultado', '').strip()
    acompanhamento.observacao = request.POST.get('observacao', '').strip()
    acompanhamento.save()
    if acompanhamento.resultado == 'Retornou à igreja':
        visitante.status_visitante = 'RETORNOU'
    else:
        visitante.status_visitante = 'ACOMPANHAMENTO'
    visitante.save(update_fields=['status_visitante', 'updated_at'])
    return redirect('visitante_detail', pk=visitante.pk)


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def visitante_nova_tentativa_view(request, pk):
    igreja = get_igreja_selecionada(request)
    visitante = get_object_or_404(visitante_queryset(igreja), pk=pk)
    if request.method == 'POST':
        AcompanhamentoVisitante.objects.create(
            igreja=igreja,
            visitante=visitante,
            tipo='RETORNO',
            data_prevista=request.POST.get('data_prevista'),
            responsavel=visitante.responsavel_visitante,
            observacao=request.POST.get('observacao', '').strip(),
        )
        return redirect('visitante_detail', pk=visitante.pk)
    return render(request, 'membros/visitante_retry.html', {'igreja': igreja, 'visitante': visitante})


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def visitante_nova_visita_view(request, pk):
    igreja = get_igreja_selecionada(request)
    visitante = get_object_or_404(visitante_queryset(igreja), pk=pk)
    if request.method == 'POST':
        VisitaVisitante.objects.create(
            igreja=igreja,
            visitante=visitante,
            data_visita=request.POST.get('data_visita') or timezone.localdate(),
            observacao=request.POST.get('observacao', '').strip(),
        )
        visitante.status_visitante = 'RETORNOU'
        visitante.save(update_fields=['status_visitante', 'updated_at'])
        return redirect('visitante_detail', pk=visitante.pk)
    return render(request, 'membros/visitante_visit.html', {'igreja': igreja, 'visitante': visitante})
