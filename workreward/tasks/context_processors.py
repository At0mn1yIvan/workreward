from tasks.utils import menu


def get_tasks_context(request):
    return {'mainmenu': menu}
