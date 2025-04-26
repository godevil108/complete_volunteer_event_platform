from django import template

register = template.Library()

@register.filter
def split(value, arg):
    return [item.strip() for item in value.split(arg)]