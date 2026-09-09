from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='portal_domain_home'),

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
