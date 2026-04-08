from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from allauth.account.views import PasswordChangeView, PasswordSetView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from user.models.user_producer import UserProducer
from django import forms
from django.views import View


class MyPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy("dashboard")


class MyPasswordSetView(LoginRequiredMixin, PasswordSetView):
    success_url = reverse_lazy("dashboard")


class MyLoginView(LoginView):
    template_name = "account/login.html" 
    redirect_authenticated_user = True


class MyLogoutView(LogoutView):
    next_page = "account_login"


# DATOS DEL USUARIO PRODUCTOR

class ProducerProfileForm(forms.ModelForm):
    class Meta:
        model = UserProducer
        fields = [
            'name', 'cuit', 'address', 'city', 'phone'
        ]


@method_decorator(login_required, name='dispatch')
class ProducerProfileView(LoginRequiredMixin, View):
    template_name = "pages/producer_profile.html"

    def get(self, request):
        if not hasattr(request.user, 'userproducer'):
            messages.error(request, "No tienes permisos para acceder a este perfil.")
            return redirect('dashboard')
        form = ProducerProfileForm(instance=request.user.userproducer)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if not hasattr(request.user, 'userproducer'):
            messages.error(request, "No tienes permisos para acceder a este perfil.")
            return redirect('dashboard')
        form = ProducerProfileForm(request.POST, instance=request.user.userproducer)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos actualizados correctamente.")
            return redirect('producer_profile')
        return render(request, self.template_name, {"form": form})

