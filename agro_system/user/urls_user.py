from django.contrib import admin
from django.urls import path, include
from dj_rest_auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils import translation


def redirect_to_admin(request):
    lang = translation.get_language() or 'es'
    return HttpResponseRedirect(f'/{lang}/admin/')

urlpatterns = [
    path('', redirect_to_admin),
]

urlpatterns = [
    #LOGIN USUARIO
    path('', include('dj_rest_auth.urls')),
    #/user/sesion/password_reset/ para resetear la contraseña
    path('password_reset/',
        PasswordResetView.as_view(),
        name='password_reset',
        ),
    path('password_reset_done/',
         PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),


]