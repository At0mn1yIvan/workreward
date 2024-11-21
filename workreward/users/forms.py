from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from users.models import ManagerCode

from django import forms


class LoginUserForm(AuthenticationForm):
    """
    Форма для аутентификации пользователя по логину или электронной почте и паролю.

    Эта форма используется для входа пользователя в систему. Она наследует функциональность
    от стандартной формы аутентификации Django (AuthenticationForm) и переопределяет поля
    для логина и пароля с дополнительными настройками.
    """

    username = forms.CharField(label="Логин | E-mail", widget=forms.TextInput())
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput())

    class Meta:
        model = get_user_model()
        fields = ["username", "password"]


class RegisterUserForm(UserCreationForm):
    """
    Форма для регистрации нового пользователя.

    Эта форма позволяет пользователю ввести логин, пароль, электронную почту, имя, фамилию, отчество,
    а также код для менеджера. Поле для кода менеджера является необязательным, и если оно
    предоставлено, выполняется проверка на правильность кода и его использование.

    Методы:
        clean_email(): Проверяет, существует ли уже пользователь с таким e-mail.
        clean_manager_code(): Проверяет правильность и неиспользованный статус кода менеджера.
        save(): Сохраняет пользователя и, если указан код менеджера, помечает его как менеджера.
    """

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
    patronymic = forms.CharField(
        label="Отчество",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Если имеется"}),
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
        }
        widgets = {
            "email": forms.TextInput(),
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
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


class ProfileUserForm(forms.ModelForm):
    """
    Форма для просмотра и редактирования профиля пользователя.

    Эта форма позволяет пользователю обновить свою личную информацию, такую как имя, фамилия и отчество.
    Поля для логина и электронной почты отображаются, но недоступны для редактирования.
    """

    username = forms.CharField(disabled=True, label="Логин", widget=forms.TextInput())
    email = forms.CharField(disabled=True, label="E-mail", widget=forms.TextInput())

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "first_name", "last_name", "patronymic"]
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "patronymic": "Отчество",
        }
        widgets = {
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "patronymic": forms.TextInput(),
        }
