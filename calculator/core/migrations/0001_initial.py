from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PrintJob",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Nome da peça"
                    ),
                ),
                (
                    "filament_price_per_kg",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "filament_weight_g",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "print_time_hours",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "labour_time_minutes",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "margin_percentage",
                    models.DecimalField(decimal_places=2, max_digits=5),
                ),
                ("cost_filament", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cost_energy", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cost_labour", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cost_machine", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cost_total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("price_final", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "consumption_kwh",
                    models.DecimalField(decimal_places=4, max_digits=10),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
