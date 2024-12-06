from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import render

# Ограничение required для классов: LoginRequiredMixin. Импорт из django.contrib.auth.mixins.


def index(request):
    welcome_text = """
    <h3>Добро пожаловать в наш сервис!</h3>

    <p><b>Work-Reward</b> - это ультимативное решение для бизнеса, позволяющее
    исполнителям и менеджерам удобным способом справляться с задачами, стоящими на повестке дня.

    Исполнители могут назнать себе задачи по силам, имея в виду, что коэффициент сложности выполнения задач будет влиять на вероятность получения премии.

    Менеджеры имеют возможность назначать исполнителей на выполнение конкретных задач, публиковать новые задачи, а так же получать отчёты о выполненных задачах.</p>
    """
    return render(
        request,
        template_name="tasks/index.html",
        context={
            "title": "Work-Reward. Главная страница",
            "welcome_text": welcome_text,
        },
    )


def about(request):
    # TODO: править текст в соответствии с реализацией.
    about_text = """
    <p>
    Тут можно ознакомиться с информацией о том, как устроены выдаваемые задачи.

    Задачи различаются по сложности и времени выполнения. За каждый из этих параметров предусмотрен надбавочный коэффициент, который влияет на размер выдаваемой премии.
    <hr>
    <h3>Ранжирование по уровню сложности задач:</h3>
    <ol>
      <li>Простой уровень сложности</li>
      <li>Средний уровень сложности</li>
      <li>Тяжелый уровень сложности</li>
      <li>Профессиональный уровень сложности</li>
    </ol>
    <hr>
    <h3>Ранжирование по времени выполнения задач:</h3>
    <ol>
      <li>Быстрая задача <i>(1 - 3 часа)</i></li>
      <li>Задача средней длительности <i>(7 - 10 часов)</i></li>
      <li>Долгосрочная задача <i>(12 часов - 3 дня)</i></li>
    </ol>
    </p>
    """

    return render(
        request,
        template_name="tasks/about.html",
        context={
            "title": "Work-Reward. О сервисе",
            "about_text": about_text,
        },
    )


@login_required
def tasks(request):
    return render(
        request,
        template_name="tasks/tasks.html",
        context={"title": "Work-Reward. Задачи"},
    )


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")
