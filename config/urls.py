from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
from apps.portal.views import portal_domain_home


urlpatterns = [
    path('', portal_domain_home, name='portal_domain_home'),

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        include('apps.core.urls')
    ),

    path(
        'accounts/',
        include('apps.accounts.urls')
    ),

    path(
        'membros/',
        include('apps.membros.urls')
    ),

    path(
        'financeiro/',
        include('apps.financeiro.urls')
    ),

    path(
        'eventos/',
        include('apps.eventos.urls')
    ),

    path('<slug:slug>/', include('apps.portal.urls')),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
