from django.contrib.auth import authenticate
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib import messages

from django.shortcuts import render
from django.shortcuts import redirect

from .models import UsuarioIgreja
from .forms import AlterarSenhaForm


def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            relacao = UsuarioIgreja.objects.filter(
                usuario=user,
                igreja_default=True,
                ativo=True
            ).first()

            if relacao:

                request.session['igreja_id'] = relacao.igreja.id

            return redirect('dashboard')

    return render(
        request,
        'accounts/login.html'
    )


def logout_view(request):

    logout(request)

    return redirect('login')


@login_required
def change_password_view(request):

    form = AlterarSenhaForm(request.user, request.POST or None)

    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'

    if request.method == 'POST' and form.is_valid():

        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Sua senha foi alterada com sucesso.')

        return redirect('dashboard')

    return render(
        request,
        'accounts/change_password.html',
        {'form': form}
    )
