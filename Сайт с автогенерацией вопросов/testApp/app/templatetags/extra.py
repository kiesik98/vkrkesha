from django import template

register = template.Library()


@register.filter
def var_type(var):
    return type(var)


@register.filter
def var_vars(var):
    return vars(var)


@register.filter
def duration(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    hours = abs(hours)
    minutes, seconds = divmod(remainder, 60)
    return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
