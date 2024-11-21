from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from users.forms import LoginUserForm, RegisterUserForm


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "users/login.html"
    extra_context = {"title": "Work-Reward. Авторизация"}


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = "users/register.html"
    extra_context = {"title": "Work-Reward. Регистрация"}
    success_url = reverse_lazy("users:login")

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


# def register(request):
#     if request.method == "POST":
#         form = RegisterUserForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.set_password(form.cleaned_data["password"])
#             user.save()
#             return render(request, template_name="users/register_done.html")
#     else:
#         form = RegisterUserForm()
#     return render(request, template_name="users/register.html", context={"form": form})


def profile(request):
    return HttpResponse("<h1>Профиль пользователя</h1>")
