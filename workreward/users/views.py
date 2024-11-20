from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from users.forms import LoginUserForm


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "users/login.html"
    extra_context = {"title": "Авторизация"}

# def login_user(request):
#     if request.method == "POST":
#         form = LoginUserForm(request.POST)
#         if form.is_valid():
#             cd = form.cleaned_data
#             user = authenticate(request, username=cd["username"], password=cd["password"])

#             if user and user.is_active:
#                 login(request, user)
#                 return HttpResponseRedirect(reverse_lazy("tasks:home"))
#     else:
#         form = LoginUserForm()
#     return render(request, template_name="users/login.html", context={'form': form})


def register(request):
    return HttpResponse("<h1>Страница регистрации</h1>")


def profile(request):
    return HttpResponse("<h1>Профиль пользователя</h1>")
