from django.conf import settings
from django.db import models


class PrintJob(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="print_jobs",
        null=True,
        blank=True,
    )
    name = models.CharField("Nome da peca", max_length=100, blank=True)
    filament_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    filament_weight_g = models.DecimalField(max_digits=10, decimal_places=2)
    print_time_hours = models.DecimalField(max_digits=10, decimal_places=2)
    labour_time_minutes = models.DecimalField(max_digits=10, decimal_places=2)
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    cost_filament = models.DecimalField(max_digits=10, decimal_places=2)
    cost_energy = models.DecimalField(max_digits=10, decimal_places=2)
    cost_labour = models.DecimalField(max_digits=10, decimal_places=2)
    cost_machine = models.DecimalField(max_digits=10, decimal_places=2)
    cost_total = models.DecimalField(max_digits=10, decimal_places=2)
    price_final = models.DecimalField(max_digits=10, decimal_places=2)
    consumption_kwh = models.DecimalField(max_digits=10, decimal_places=4)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        if self.name:
            return self.name
        return f"Peca #{self.pk}"
