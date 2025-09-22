from django import forms

from .models import FilamentType, PrintJob

FILAMENT_TYPE_CHOICES = [
    ('PLA', 'PLA'),
    ('PLA+', 'PLA+'),
    ('PLA Silk', 'PLA Silk'),
    ('PLA Wood', 'PLA Wood'),
    ('PLA Metal', 'PLA Metal'),
    ('PLA Glow', 'PLA Glow'),
    ('PLA Transparente', 'PLA Transparente'),
    ('ABS', 'ABS'),
    ('PETG', 'PETG'),
    ('TPU / TPE', 'TPU / TPE'),
    ('Nylon (PA)', 'Nylon (PA)'),
    ('Carbon Fiber', 'Carbon Fiber'),
    ('Glass Fiber', 'Glass Fiber'),
    ('Metal Filled', 'Metal Filled'),
    ('Wood Filled', 'Wood Filled'),
]


class PrintJobForm(forms.Form):
    piece_name = forms.CharField(
        label="Nome da Pe\u00e7a",
        max_length=100,
        required=False,
    )
    filament_type = forms.ModelChoiceField(
        label="Filamento",
        queryset=FilamentType.objects.none(),
        help_text="Selecione um filamento guardado no inventário.",
    )
    filament_weight_g = forms.DecimalField(
        label="Filamento (g)",
        min_value=0,
        decimal_places=2,
        max_digits=10,
    )
    print_time_hours = forms.DecimalField(
        label="Tempo (h)",
        min_value=0,
        decimal_places=2,
        max_digits=10,
    )
    labour_time_minutes = forms.DecimalField(
        label="Mão de Obra (min)",
        min_value=0,
        decimal_places=2,
        max_digits=10,
    )
    margin_percentage = forms.DecimalField(
        label="Margem (%)",
        min_value=0,
        max_value=99,
        decimal_places=2,
        max_digits=5,
        help_text="Use valores inferiores a 100.",
    )

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
            filament_field.empty_label = "Sem filamentos no inventário"
            filament_field.help_text = "Adicione filamentos no inventário antes de calcular."
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
                filament_field.help_text = "Selecione um filamento guardado no inventário."

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault("step", "0.01")

    def clean_piece_name(self):
        name = (self.cleaned_data.get("piece_name") or "").strip()
        if not name:
            return ""

        existing_piece = getattr(self, "existing_piece", None)
        target_user = getattr(self, "user", None)
        if existing_piece is not None and existing_piece.user is not None:
            target_user = existing_piece.user

        qs = PrintJob.objects.all()
        if target_user is not None:
            qs = qs.filter(user=target_user)
        else:
            qs = qs.filter(user__isnull=True)
        if existing_piece is not None:
            qs = qs.exclude(pk=existing_piece.pk)
        if qs.filter(name__iexact=name).exists():
            raise forms.ValidationError("Ja existe uma pe\u00e7a com este nome.")
        return name

    def clean_margin_percentage(self):
        value = self.cleaned_data["margin_percentage"]
        if value >= 100:
            raise forms.ValidationError("A margem deve ser inferior a 100%.")
        return value


class PieceImportForm(forms.Form):
    file = forms.FileField(
        label="Ficheiro Excel",
        help_text="Envie um ficheiro .xlsx com as colunas: piece_name, filament_price_per_kg, filament_weight_g, print_time_hours, labour_time_minutes, margin_percentage.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["file"]
        field.widget.attrs.setdefault("class", "form-control")
        field.widget.attrs.setdefault("accept", ".xlsx")


class FilamentTypeForm(forms.ModelForm):
    name = forms.ChoiceField(choices=FILAMENT_TYPE_CHOICES, label='Tipo')

    class Meta:
        model = FilamentType
        fields = ['name', 'color', 'price_per_kg', 'weight_kg']
        labels = {
            'color': 'Cor',
            'price_per_kg': 'Preço (EUR/kg)',
            'weight_kg': 'Peso (kg)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.setdefault('class', 'form-select')
        for field_name, field in self.fields.items():
            if field_name == 'name':
                continue
            field.widget.attrs.setdefault('class', 'form-control')
            if isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault('step', '0.01')


class InventoryQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        label='Quantidade',
        min_value=1,
        initial=1,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['quantity']
        field.widget.attrs.setdefault('class', 'form-control')



