from django.urls import path

from .views import dashboard_view
from .views import exportar_faixa_etaria_excel_view
from .views import exportar_visitantes_excel_view
from .views import home_view
from .views import selecionar_igreja_view


urlpatterns = [

    path(
        '',
        home_view,
        name='home'
    ),

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
