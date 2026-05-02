from django import template

register = template.Library()


@register.filter
def currency(value):
    try:
        return f"PHP {float(value):,.2f}"
    except (TypeError, ValueError):
        return "PHP 0.00"


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0
