from django import forms


class PrintJobForm(forms.Form):
    piece_name = forms.CharField(
        label="Nome da Peça",
        max_length=100,
        required=False,
    )
    filament_price_per_kg = forms.DecimalField(
        label="Filamento (EUR/kg)",
        min_value=0,
        decimal_places=2,
        max_digits=10,
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
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault("step", "0.01")

    def clean_margin_percentage(self):
        value = self.cleaned_data["margin_percentage"]
        if value >= 100:
            raise forms.ValidationError("A margem deve ser inferior a 100%.")
        return value


class PieceImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Ficheiro CSV",
        help_text="Formato: piece_name, filament_price_per_kg, filament_weight_g, print_time_hours, labour_time_minutes, margin_percentage",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["csv_file"].widget.attrs.setdefault("class", "form-control")
        self.fields["csv_file"].widget.attrs.setdefault("accept", ".csv")
