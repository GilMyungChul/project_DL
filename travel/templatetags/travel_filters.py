from django import template

register = template.Library()

@register.filter
def first_image(url_string):
    if not url_string:
        return ""
    return url_string.split(",")[0].strip()

@register.filter
def trim_last_comma(value):
    """URL 끝의 쉼표 제거"""
    if value and value.endswith(","):
        return value[:-1]
    return value