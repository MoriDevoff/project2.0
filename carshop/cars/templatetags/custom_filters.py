from django import template

register = template.Library()

@register.filter
def startswith(text, prefix):
    return text.startswith(prefix)

@register.filter
def lookup(obj, key):
    return obj[key]

@register.filter
def map(queryset, field_name):
    """
    Извлекает указанное поле из каждого объекта в queryset.
    Пример: car.favorite_set.all|map:'user' вернёт список пользователей.
    """
    return [getattr(item, field_name) for item in queryset]