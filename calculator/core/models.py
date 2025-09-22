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
    name = models.CharField("Nome da peça", max_length=100, blank=True)
    filament_type = models.ForeignKey(
        'FilamentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='print_jobs',
    )
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
        return f"Peça #{self.pk}"

class FilamentType(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filament_types',
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=50, blank=True)
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.color})" if self.color else self.name


class InventoryItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inventory_items',
    )
    print_job = models.ForeignKey(
        PrintJob,
        on_delete=models.CASCADE,
        related_name='inventory_records',
    )
    piece_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'print_job'],
                name='uniq_inventory_item_user_piece',
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.piece_name} x{self.quantity}"
