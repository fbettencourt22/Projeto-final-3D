from pathlib import Path
from textwrap import dedent

path = Path('calculator/core/forms.py')
text = path.read_text(encoding='utf-8')
old = dedent('''
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        filament_qs = FilamentType.objects.all().order_by("name")
        if user and not getattr(user, "is_superuser", False):
            filament_qs = filament_qs.filter(user=user)
        filament_field = self.fields["filament_type"]
        filament_field.queryset = filament_qs
        filament_field.empty_label = "Escolha um filamento"

        if not filament_qs.exists():
            filament_field.empty_label = "Sem filamentos no inventario"
            filament_field.help_text = "Adicione filamentos no inventario antes de calcular."
        else:
            selected_value = None
            if self.is_bound:
                selected_value = self.data.get(self.add_prefix("filament_type"))
            else:
                initial_value = self.initial.get("filament_type")
                if initial_value is not None:
                    selected_value = getattr(initial_value, "pk", initial_value)
            if selected_value:
                filament_field.help_text = ""
            else:
                filament_field.help_text = "Selecione um filamento guardado no inventario."


        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault("step", "0.01")
''')
new = dedent('''
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        existing_piece = kwargs.pop("existing_piece", None)
        super().__init__(*args, **kwargs)

        self.user = user
        self.existing_piece = existing_piece

        filament_qs = FilamentType.objects.all().order_by("name")
        if user and not getattr(user, "is_superuser", False):
            filament_qs = filament_qs.filter(user=user)
        filament_field = self.fields["filament_type"]
        filament_field.queryset = filament_qs
        filament_field.empty_label = "Escolha um filamento"

        if not filament_qs.exists():
            filament_field.empty_label = "Sem filamentos no inventario"
            filament_field.help_text = "Adicione filamentos no inventario antes de calcular."
        else:
            selected_value = None
            if self.is_bound:
                selected_value = self.data.get(self.add_prefix("filament_type"))
            else:
                initial_value = self.initial.get("filament_type")
                if initial_value is not None:
                    selected_value = getattr(initial_value, "pk", initial_value)
            if selected_value:
                filament_field.help_text = ""
            else:
                filament_field.help_text = "Selecione um filamento guardado no inventario."

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault("step", "0.01")
''')
if old not in text:
    raise SystemExit('target block not found for __init__ update')
text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
