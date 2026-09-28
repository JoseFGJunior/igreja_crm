from django.urls import path
from . import views
app_name = 'mobile_api'
urlpatterns = [path('home/', views.home, name='home'), path('palavra-do-dia/', views.palavra_do_dia, name='palavra-do-dia'), path('prototipo/', views.prototipo, name='prototipo'), path('pedidos-oracao/', views.pedidos_oracao, name='pedidos-oracao')]