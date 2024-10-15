from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import render

# Create your views here.


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")


def index(request):
    return HttpResponse("<h1>Стартовая страница сервиса</h1>")
