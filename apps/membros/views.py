from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from apps.accounts.models import UsuarioIgreja
from apps.membros.forms import MembroForm
from apps.membros.models import Membro


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
def membro_list_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    pesquisa = request.GET.get('q', '').strip()

    membros = Membro.objects.filter(
        igreja=igreja
    ).order_by(
        'nome'
    )

    if pesquisa:
        membros = membros.filter(
            nome__icontains=pesquisa
        )

    return render(
        request,
        'membros/membro_list.html',
        {
            'igreja': igreja,
            'membros': membros,
            'pesquisa': pesquisa,
        }
    )


@login_required
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
