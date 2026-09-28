from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def brl(value):
    """Format a numeric value using Brazilian currency separators."""
    if value is None or value == '':
        return '0,00'

    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return '0,00'

    formatted = f'{number:,.2f}'
    return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
