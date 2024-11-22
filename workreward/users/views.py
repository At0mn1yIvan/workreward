from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from users.forms import (LoginUserForm, ProfileUserForm, RegisterUserForm,
                         UserPasswordChangeForm)


class LoginUser(LoginView):
    """
    Представление для авторизации пользователей на сайте.

    Этот класс предоставляет форму для авторизации пользователя. Он наследуется
    от LoginView и использует форму LoginUserForm для сбора данных, таких как логин
    или электронная почта и пароль. После успешной авторизации пользователя
    осуществляется перенаправление на главную страницу сервиса.

    Атрибуты:
        form_class (LoginUserForm): Форма для ввода логина и пароля пользователя.
        template_name (str): Путь к HTML-шаблону страницы авторизации.
        extra_context (dict): Дополнительный контекст, передаваемый в шаблон. Включает заголовок страницы.
    """

    form_class = LoginUserForm
    template_name = "users/login.html"
    extra_context = {"title": "Work-Reward. Авторизация"}


class RegisterUser(CreateView):
    """
    Представление для регистрации нового пользователя.

    Этот класс предоставляет форму для регистрации нового пользователя. Он наследуется
    от CreateView и использует форму RegisterUserForm для сбора данных, таких как логин, фамилия, имя, отчество,
    пароль, электронная почта и код для менеджера. После успешной регистрации пользователя
    осуществляется перенаправление на страницу с подтверждением регистрации.

    Атрибуты:
        form_class (forms.ModelForm): Форма, используемая для регистрации нового пользователя.
        template_name (str): Путь к шаблону, который отображает страницу регистрации.
        extra_context (dict): Дополнительный контекст для шаблона, например, заголовок страницы.
        success_url (str): URL для перенаправления после успешной регистрации пользователя.
    """

    form_class = RegisterUserForm
    template_name = "users/register.html"
    extra_context = {"title": "Work-Reward. Регистрация"}
    success_url = reverse_lazy("users:register_done")


def register_done(request):
    context = {"title": "Work-Reward. Успешная регистрация"}
    return render(request, template_name="users/register_done.html", context=context)


class ProfileUser(LoginRequiredMixin, UpdateView):
    """
    Представление для обновления профиля пользователя.

    Этот класс наследуется от UpdateView и позволяет пользователю обновить
    свой профиль, включая имя, фамилию и отчество. Поля для логина и
    электронной почты недоступны для редактирования (они отображаются только для просмотра).
    Доступ к этому представлению ограничен только аутентифицированными пользователями,
    что обеспечивается с помощью LoginRequiredMixin.

    Атрибуты:
        model (Model): Модель пользователя, которая будет обновляться.
        form_class (forms.ModelForm): Форма, используемая для обновления данных пользователя.
        template_name (str): Путь к шаблону, который используется для отображения страницы профиля.
        extra_context (dict): Дополнительный контекст для передачи в шаблон (например, заголовок страницы).

    Методы:
        get_success_url(): Возвращает URL для перенаправления после успешного обновления профиля.
        get_object(queryset=None): Возвращает текущего аутентифицированного пользователя для редактирования.
    """

    model = get_user_model()
    form_class = ProfileUserForm
    template_name = "users/profile.html"
    extra_context = {"title": "Work-Reward. Профиль пользователя"}
    success_url = reverse_lazy("users:profile")
    # def get_success_url(self):
    #     return reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    template_name = "users/password_change_form.html"
    extra_context = {"title": "Work-Reward. Смена пароля"}
    success_url = reverse_lazy("users:password_change_done")

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
