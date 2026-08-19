from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout

from django.shortcuts import render
from django.shortcuts import redirect

from .models import UsuarioIgreja


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
