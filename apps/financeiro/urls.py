from django.urls import path

from apps.financeiro.views import categoria_entrada_create_view
from apps.financeiro.views import categoria_entrada_list_view
from apps.financeiro.views import categoria_entrada_update_view
from apps.financeiro.views import categoria_saida_create_view
from apps.financeiro.views import categoria_saida_list_view
from apps.financeiro.views import categoria_saida_update_view
from apps.financeiro.views import conta_pagar_create_view
from apps.financeiro.views import conta_pagar_delete_view
from apps.financeiro.views import conta_pagar_list_view
from apps.financeiro.views import conta_pagar_update_view
from apps.financeiro.views import despesa_recorrente_create_view
from apps.financeiro.views import entrada_create_view
from apps.financeiro.views import entrada_delete_view
from apps.financeiro.views import entrada_list_view
from apps.financeiro.views import entrada_update_view
from apps.financeiro.views import financeiro_dashboard_view
from apps.financeiro.views import resumo_anual_excel_view
from apps.financeiro.views import fechamento_mensal_view
from apps.financeiro.views import fechamento_confirmar_view
from apps.financeiro.views import fechamento_reabrir_view
from apps.financeiro.views import fechamento_reprocessar_view
from apps.financeiro.views import fechamento_configurar_saldo_inicial_view


urlpatterns = [

    path(
        '',
        financeiro_dashboard_view,
        name='financeiro_dashboard'
    ),

    path(
        'resumo-anual/excel/',
        resumo_anual_excel_view,
        name='financeiro_resumo_anual_excel'
    ),

    path('fechamento-mensal/', fechamento_mensal_view, name='financeiro_fechamento_mensal'),
    path('fechamento-mensal/confirmar/', fechamento_confirmar_view, name='financeiro_fechamento_confirmar'),
    path('fechamento-mensal/<int:pk>/reabrir/', fechamento_reabrir_view, name='financeiro_fechamento_reabrir'),
    path('fechamento-mensal/<int:pk>/reprocessar/', fechamento_reprocessar_view, name='financeiro_fechamento_reprocessar'),
    path('fechamento-mensal/<int:pk>/saldo-inicial/', fechamento_configurar_saldo_inicial_view, name='financeiro_fechamento_configurar_saldo_inicial'),

    path(
        'entradas/',
        entrada_list_view,
        name='financeiro_entrada_list'
    ),

    path(
        'entradas/nova/',
        entrada_create_view,
        name='financeiro_entrada_create'
    ),

    path(
        'entradas/<int:pk>/editar/',
        entrada_update_view,
        name='financeiro_entrada_update'
    ),

    path(
        'entradas/<int:pk>/excluir/',
        entrada_delete_view,
        name='financeiro_entrada_delete'
    ),

    path(
        'entradas/categorias/',
        categoria_entrada_list_view,
        name='financeiro_categoria_entrada_list'
    ),

    path(
        'entradas/categorias/nova/',
        categoria_entrada_create_view,
        name='financeiro_categoria_entrada_create'
    ),

    path(
        'entradas/categorias/<int:pk>/editar/',
        categoria_entrada_update_view,
        name='financeiro_categoria_entrada_update'
    ),

    path(
        'contas-a-pagar/',
        conta_pagar_list_view,
        name='financeiro_conta_pagar_list'
    ),

    path(
        'contas-a-pagar/nova/',
        conta_pagar_create_view,
        name='financeiro_conta_pagar_create'
    ),

    path(
        'contas-a-pagar/recorrente/nova/',
        despesa_recorrente_create_view,
        name='financeiro_despesa_recorrente_create'
    ),

    path(
        'contas-a-pagar/<int:pk>/editar/',
        conta_pagar_update_view,
        name='financeiro_conta_pagar_update'
    ),

    path(
        'contas-a-pagar/<int:pk>/excluir/',
        conta_pagar_delete_view,
        name='financeiro_conta_pagar_delete'
    ),

    path(
        'contas-a-pagar/categorias/',
        categoria_saida_list_view,
        name='financeiro_categoria_saida_list'
    ),

    path(
        'contas-a-pagar/categorias/nova/',
        categoria_saida_create_view,
        name='financeiro_categoria_saida_create'
    ),

    path(
        'contas-a-pagar/categorias/<int:pk>/editar/',
        categoria_saida_update_view,
        name='financeiro_categoria_saida_update'
    ),

]
