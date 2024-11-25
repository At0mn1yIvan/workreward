from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import render

# Ограничение reqiured для классов: LoginRequiredMixin. Импорт из django.contrib.auth.mixins.


def index(request):
    return render(request,
                  template_name="tasks/index.html",
                  context={"title": "Work-Reward. Главная страница"}
                  )


@login_required
def tasks(request):
    return render(request,
                  template_name="tasks/tasks.html",
                  context={"title": "Work-Reward. Задачи"}
                  )


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")
