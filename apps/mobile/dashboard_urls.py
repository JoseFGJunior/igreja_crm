from django.urls import path

from .views import acesso_dashboard_view, mensagem_dashboard_view


urlpatterns = [
    path('', mensagem_dashboard_view, name='mensagem_dashboard'),
    path('acessos/', acesso_dashboard_view, name='acesso_dashboard'),
]
