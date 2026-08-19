from django.conf import settings

from apps.accounts.models import UsuarioIgreja


def environment(request):
    return {
        'environment': settings.ENVIRONMENT,
        'environment_display': settings.ENVIRONMENT_DISPLAY,
    }


def igreja_atual(request):
    if not request.user.is_authenticated:
        return {
            'igreja_atual': None,
            'plano_completo_ativo': False,
        }

    igreja_id = request.session.get('igreja_id')

    if not igreja_id:
        return {
            'igreja_atual': None,
            'plano_completo_ativo': False,
        }

    relacao = UsuarioIgreja.objects.select_related('igreja').filter(
        usuario=request.user,
        igreja_id=igreja_id,
        ativo=True,
        igreja__ativa=True
    ).first()

    igreja = relacao.igreja if relacao else None

    return {
        'igreja_atual': igreja,
        'plano_completo_ativo': bool(
            igreja and igreja.plano_completo_ativo
        ),
    }
