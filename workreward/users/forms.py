from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from users.models import ManagerCode
from datetime import datetime


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput())
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput())

    class Meta:
        model = get_user_model()
        fields = ["username", "password"]


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput())
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput())
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput())
    manager_code = forms.CharField(
        label="Код для менеджера",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Оставьте пустым, если вы не менеджер"}
        ),
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "password1",
            "password2",
            "manager_code",
        ]
        labels = {
            "email": "E-mail",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "patronymic": "Отчество",
        }
        widgets = {
            "email": forms.TextInput(),
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "patronymic": forms.TextInput(),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Такой E-mail уже существует")
        return email

    def clean_manager_code(self):
        code = self.cleaned_data.get("manager_code")
        if code:
            try:
                manager_code = ManagerCode.objects.get(code=code, is_used=False)
                return manager_code
            except ManagerCode.DoesNotExist:
                raise forms.ValidationError("Неверный или использованный код")
        return None

    def save(self, commit=True):
        user = super().save(commit=False)
        manager_code = self.cleaned_data.get("manager_code")

        if manager_code:
            user.is_manager = True
            manager_code.is_used = True
            manager_code.used_at = datetime.now()
            manager_code.save()

        if commit:
            user.save()

        return user
