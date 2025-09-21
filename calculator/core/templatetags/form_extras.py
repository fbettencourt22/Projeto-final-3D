from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    widget = field.field.widget
    existing = widget.attrs.get("class", "")
    classes = f"{existing} {css_class}".strip()
    return field.as_widget(attrs={"class": classes})
