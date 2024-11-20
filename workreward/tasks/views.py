from django.http import HttpResponseNotFound
from django.shortcuts import render


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")


def index(request):
    return render(request, template_name="tasks/index.html")


def tasks(request):
    return render(request, template_name="tasks/tasks.html")
