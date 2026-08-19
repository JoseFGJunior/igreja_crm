from django.urls import path

from apps.membros.views import membro_create_view
from apps.membros.views import membro_delete_view
from apps.membros.views import membro_list_view
from apps.membros.views import membro_update_view


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
        '<int:pk>/editar/',
        membro_update_view,
        name='membro_update'
    ),

    path(
        '<int:pk>/excluir/',
        membro_delete_view,
        name='membro_delete'
    ),

]
