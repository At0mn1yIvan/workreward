from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def active_class(context, url_name):
    view_name = context["request"].resolver_match.view_name
    return "active" if view_name == url_name else ""
