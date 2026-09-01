from django.urls import path

from .views import (
    login_view,
    logout_view,
    change_password_view,
)

urlpatterns = [

    path(
        'login/',
        login_view,
        name='login'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

    path(
        'alterar-senha/',
        change_password_view,
        name='change_password'
    ),

]
