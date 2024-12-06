from tasks.utils import menu


def get_tasks_context(request) -> dict[str, list[dict[str, str]]]:
    return {'mainmenu': menu}
