from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


urlpatterns = [

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

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
