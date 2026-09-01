from django.urls import path
from django.views.generic import RedirectView

from .views import dashboard_view
from .views import exportar_faixa_etaria_excel_view
from .views import exportar_visitantes_excel_view
from .views import home_view
from .views import selecionar_igreja_view
from .views import aniversario_mensagem_view


urlpatterns = [

    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),

    path(
        'dashboard/',
        dashboard_view,
        name='dashboard'
    ),

    path(
        'selecionar-igreja/',
        selecionar_igreja_view,
        name='selecionar_igreja'
    ),

    path(
        'dashboard/aniversariantes/mensagem/',
        aniversario_mensagem_view,
        name='aniversario_mensagem'
    ),

    path(
        'membros/faixa-etaria/excel/',
        exportar_faixa_etaria_excel_view,
        name='exportar_faixa_etaria_excel'
    ),

    path(
        'membros/visitantes/excel/',
        exportar_visitantes_excel_view,
        name='exportar_visitantes_excel'
    ),

]
