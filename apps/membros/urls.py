from django.urls import path

from apps.membros.views import membro_create_view
from apps.membros.views import membro_delete_view
from apps.membros.views import identificar_membro_view
from apps.membros.views import membro_list_view
from apps.membros.views import membro_update_view
from apps.membros.views import visitante_contato_view
from apps.membros.views import visitante_create_view
from apps.membros.views import visitante_acompanhamentos_view
from apps.membros.views import visitante_dashboard_view
from apps.membros.views import visitante_detail_view
from apps.membros.views import visitante_list_view
from apps.membros.views import visitante_mensagens_view
from apps.membros.views import visitante_nova_tentativa_view
from apps.membros.views import visitante_nova_visita_view
from apps.membros.views import visitante_update_view
from apps.membros.views import pedido_oracao_list_view, pedido_oracao_create_view, pedido_oracao_update_view, pedido_oracao_toggle_view, pedido_oracao_delete_view


urlpatterns = [

    path(
        '',
        membro_list_view,
        name='membro_list'
    ),

    path(
        'novo/',
        membro_create_view,
        name='membro_create'
    ),

    path(
        'identificar/',
        identificar_membro_view,
        name='identificar_membro'
    ),

    path(
        '<int:pk>/editar/',
        membro_update_view,
        name='membro_update'
    ),

    path(
        '<int:pk>/excluir/',
        membro_delete_view,
        name='membro_delete'
    ),

    path('visitantes/', visitante_dashboard_view, name='visitante_dashboard'),
    path('visitantes/lista/', visitante_list_view, name='visitante_list'),
    path('visitantes/acompanhamentos/', visitante_acompanhamentos_view, name='visitante_acompanhamentos'),
    path('visitantes/mensagens/', visitante_mensagens_view, name='visitante_mensagens'),
    path('visitantes/novo/', visitante_create_view, name='visitante_create'),
    path('visitantes/<int:pk>/', visitante_detail_view, name='visitante_detail'),
    path('visitantes/<int:pk>/editar/', visitante_update_view, name='visitante_update'),
    path('visitantes/<int:pk>/contato/', visitante_contato_view, name='visitante_contato'),
    path('visitantes/<int:pk>/nova-tentativa/', visitante_nova_tentativa_view, name='visitante_nova_tentativa'),
    path('visitantes/<int:pk>/nova-visita/', visitante_nova_visita_view, name='visitante_nova_visita'),
    path('pedidos-oracao/', pedido_oracao_list_view, name='pedido_oracao_list'),
    path('pedidos-oracao/novo/', pedido_oracao_create_view, name='pedido_oracao_create'),
    path('pedidos-oracao/<int:pk>/editar/', pedido_oracao_update_view, name='pedido_oracao_update'),
    path('pedidos-oracao/<int:pk>/alternar-atendimento/', pedido_oracao_toggle_view, name='pedido_oracao_toggle'),
    path('pedidos-oracao/<int:pk>/excluir/', pedido_oracao_delete_view, name='pedido_oracao_delete'),

]
