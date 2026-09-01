from django.urls import path

from apps.eventos.views import calendario_json_view, calendario_view, evento_create_view, evento_delete_view, evento_detail_view, evento_update_view, eventos_exportar_excel_view


urlpatterns = [
    path('', calendario_view, name='eventos_calendario'),
    path('calendario/', calendario_json_view, name='eventos_calendario_json'),
    path('exportar-excel/', eventos_exportar_excel_view, name='eventos_exportar_excel'),
    path('novo/', evento_create_view, name='evento_create'),
    path('<int:pk>/', evento_detail_view, name='evento_detail'),
    path('<int:pk>/editar/', evento_update_view, name='evento_update'),
    path('<int:pk>/excluir/', evento_delete_view, name='evento_delete'),
]
