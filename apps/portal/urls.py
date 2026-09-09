from django.urls import path
from .views import portal
urlpatterns=[
 path('',portal,name='portal_home'),
 path('quem-somos/',portal,name='portal_quem_somos'),
 path('programacao/',portal,name='portal_programacao'),
 path('eventos/',portal,name='portal_eventos'),
 path('contato/',portal,name='portal_contato'),
]