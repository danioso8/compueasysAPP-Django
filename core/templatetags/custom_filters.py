from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Split a string by the given argument"""
    return value.split(arg)

@register.filter(name='trim')
def trim(value):
    """Remove whitespace from string"""
    return value.strip() if value else value

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
