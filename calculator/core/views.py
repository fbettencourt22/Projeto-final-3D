import csv
import io
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import PieceImportForm, PrintJobForm
from .models import PrintJob

VALOR_KWH = Decimal("0.158")
CONSUMO_W = Decimal("140")
CUSTO_MAO_OBRA = Decimal("20")
DESPERDICIO_FILAMENTO = Decimal("0.10")
CUSTO_MAQUINA_HORA = Decimal("0.20")

IMPORT_COLUMNS = [
    "piece_name",
    "filament_price_per_kg",
    "filament_weight_g",
    "print_time_hours",
    "labour_time_minutes",
    "margin_percentage",
]


def to_currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_print_job(data: dict) -> dict:
    filament_price_per_kg = Decimal(data["filament_price_per_kg"])
    filament_weight_g = Decimal(data["filament_weight_g"])
    print_time_hours = Decimal(data["print_time_hours"])
    labour_time_minutes = Decimal(data["labour_time_minutes"])
    margin_percentage = Decimal(data["margin_percentage"])

    cost_filament = (filament_price_per_kg / Decimal("1000")) * filament_weight_g
    cost_filament *= Decimal("1") + DESPERDICIO_FILAMENTO

    consumption_kwh = (CONSUMO_W * print_time_hours) / Decimal("1000")
    cost_energy = consumption_kwh * VALOR_KWH

    cost_labour = (labour_time_minutes / Decimal("60")) * CUSTO_MAO_OBRA
    cost_machine = print_time_hours * CUSTO_MAQUINA_HORA

    cost_total = cost_filament + cost_energy + cost_labour + cost_machine
    price_final = cost_total / (Decimal("1") - (margin_percentage / Decimal("100")))

    return {
        "cost_filament": to_currency(cost_filament),
        "cost_energy": to_currency(cost_energy),
        "cost_labour": to_currency(cost_labour),
        "cost_machine": to_currency(cost_machine),
        "cost_total": to_currency(cost_total),
        "price_final": to_currency(price_final),
        "consumption_kwh": consumption_kwh.quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        ),
    }


def piece_permission_check(user, piece: PrintJob):
    if user.is_superuser:
        return True
    return piece.user == user


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def calculator_view(request):
    result = None

    if request.method == "POST":
        form = PrintJobForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            result = calculate_print_job(cleaned)

            print_job = PrintJob.objects.create(
                user=request.user,
                name=cleaned.get("piece_name", ""),
                filament_price_per_kg=cleaned["filament_price_per_kg"],
                filament_weight_g=cleaned["filament_weight_g"],
                print_time_hours=cleaned["print_time_hours"],
                labour_time_minutes=cleaned["labour_time_minutes"],
                margin_percentage=cleaned["margin_percentage"],
                cost_filament=result["cost_filament"],
                cost_energy=result["cost_energy"],
                cost_labour=result["cost_labour"],
                cost_machine=result["cost_machine"],
                cost_total=result["cost_total"],
                price_final=result["price_final"],
                consumption_kwh=result["consumption_kwh"],
            )

            result["piece_name"] = print_job.name or f"Peça #{print_job.pk}"
            result["created_at"] = print_job.created_at

            form = PrintJobForm()
    else:
        form = PrintJobForm()

    pieces_qs = PrintJob.objects.select_related("user")
    if not request.user.is_superuser:
        pieces_qs = pieces_qs.filter(user=request.user)
    pieces = pieces_qs

    context = {
        "form": form,
        "result": result,
        "pieces": pieces,
        "constants": {
            "VALOR_KWH": VALOR_KWH,
            "CONSUMO_W": CONSUMO_W,
            "CUSTO_MAO_OBRA": CUSTO_MAO_OBRA,
            "DESPERDICIO_FILAMENTO": DESPERDICIO_FILAMENTO,
            "CUSTO_MAQUINA_HORA": CUSTO_MAQUINA_HORA,
        },
    }
    return render(request, "core/calculator.html", context)


@login_required
def pieces_list_view(request):
    pieces_qs = PrintJob.objects.select_related("user")
    if not request.user.is_superuser:
        pieces_qs = pieces_qs.filter(user=request.user)
    context = {"pieces": pieces_qs}
    return render(request, "core/pieces_list.html", context)


@login_required
def piece_edit_view(request, pk: int):
    piece = get_object_or_404(PrintJob.objects.select_related("user"), pk=pk)
    if not piece_permission_check(request.user, piece):
        return HttpResponseForbidden("Sem permissao.")

    initial = {
        "piece_name": piece.name,
        "filament_price_per_kg": piece.filament_price_per_kg,
        "filament_weight_g": piece.filament_weight_g,
        "print_time_hours": piece.print_time_hours,
        "labour_time_minutes": piece.labour_time_minutes,
        "margin_percentage": piece.margin_percentage,
    }

    if request.method == "POST":
        form = PrintJobForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            result = calculate_print_job(cleaned)

            piece.name = cleaned.get("piece_name", "")
            piece.filament_price_per_kg = cleaned["filament_price_per_kg"]
            piece.filament_weight_g = cleaned["filament_weight_g"]
            piece.print_time_hours = cleaned["print_time_hours"]
            piece.labour_time_minutes = cleaned["labour_time_minutes"]
            piece.margin_percentage = cleaned["margin_percentage"]
            piece.cost_filament = result["cost_filament"]
            piece.cost_energy = result["cost_energy"]
            piece.cost_labour = result["cost_labour"]
            piece.cost_machine = result["cost_machine"]
            piece.cost_total = result["cost_total"]
            piece.price_final = result["price_final"]
            piece.consumption_kwh = result["consumption_kwh"]
            if piece.user is None:
                piece.user = request.user
            piece.save()
            return redirect("pieces_list")
    else:
        form = PrintJobForm(initial=initial)

    return render(request, "core/piece_form.html", {"form": form, "piece": piece})


@login_required
def piece_delete_view(request, pk: int):
    piece = get_object_or_404(PrintJob.objects.select_related("user"), pk=pk)
    if not piece_permission_check(request.user, piece):
        return HttpResponseForbidden("Sem permissao.")

    if request.method == "POST":
        piece.delete()
        return redirect("pieces_list")

    return render(request, "core/piece_confirm_delete.html", {"piece": piece})


@login_required
def piece_export_view(request):
    pieces = PrintJob.objects.select_related("user")
    if not request.user.is_superuser:
        pieces = pieces.filter(user=request.user)

    response = HttpResponse(content_type="text/csv")
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = (
        f'attachment; filename="pecas_{timestamp}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "piece_name",
            "filament_price_per_kg",
            "filament_weight_g",
            "print_time_hours",
            "labour_time_minutes",
            "margin_percentage",
            "cost_filament",
            "cost_energy",
            "cost_labour",
            "cost_machine",
            "cost_total",
            "price_final",
            "consumption_kwh",
            "created_at",
            "owner",
        ]
    )

    for piece in pieces:
        writer.writerow(
            [
                piece.name or "",
                piece.filament_price_per_kg,
                piece.filament_weight_g,
                piece.print_time_hours,
                piece.labour_time_minutes,
                piece.margin_percentage,
                piece.cost_filament,
                piece.cost_energy,
                piece.cost_labour,
                piece.cost_machine,
                piece.cost_total,
                piece.price_final,
                piece.consumption_kwh,
                piece.created_at.isoformat(),
                piece.user.get_username() if piece.user else "",
            ]
        )

    return response


@login_required
def piece_import_view(request):
    form = PieceImportForm()
    errors = []

    if request.method == "POST":
        form = PieceImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data["csv_file"]
            try:
                data = uploaded.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                errors.append("Não foi possível ler o ficheiro como UTF-8.")
                data = ""

            if data:
                reader = csv.DictReader(io.StringIO(data))
                missing = [col for col in IMPORT_COLUMNS if col not in reader.fieldnames]
                if missing:
                    errors.append(
                        "Colunas em falta: " + ", ".join(missing)
                    )
                else:
                    created = 0
                    for idx, row in enumerate(reader, start=2):
                        try:
                            payload = {
                                "piece_name": row.get("piece_name", "").strip(),
                                "filament_price_per_kg": row["filament_price_per_kg"],
                                "filament_weight_g": row["filament_weight_g"],
                                "print_time_hours": row["print_time_hours"],
                                "labour_time_minutes": row["labour_time_minutes"],
                                "margin_percentage": row["margin_percentage"],
                            }
                            for key in [
                                "filament_price_per_kg",
                                "filament_weight_g",
                                "print_time_hours",
                                "labour_time_minutes",
                                "margin_percentage",
                            ]:
                                payload[key] = Decimal(payload[key])

                            if payload["margin_percentage"] >= Decimal("100"):
                                raise ValueError("Margem deve ser inferior a 100%.")


                            result = calculate_print_job(payload)

                            PrintJob.objects.create(
                                user=request.user,
                                name=payload["piece_name"],
                                filament_price_per_kg=payload["filament_price_per_kg"],
                                filament_weight_g=payload["filament_weight_g"],
                                print_time_hours=payload["print_time_hours"],
                                labour_time_minutes=payload["labour_time_minutes"],
                                margin_percentage=payload["margin_percentage"],
                                cost_filament=result["cost_filament"],
                                cost_energy=result["cost_energy"],
                                cost_labour=result["cost_labour"],
                                cost_machine=result["cost_machine"],
                                cost_total=result["cost_total"],
                                price_final=result["price_final"],
                                consumption_kwh=result["consumption_kwh"],
                            )
                            created += 1
                        except Exception as exc:  # noqa: BLE001
                            errors.append(
                                f"Linha {idx}: {exc}"
                            )

                    if created:
                        messages.success(
                            request,
                            f"Importadas {created} peça(s) para o seu utilizador.",
                        )
                        if not errors:
                            return redirect("pieces_list")

    return render(
        request,
        "core/piece_import.html",
        {
            "form": form,
            "errors": errors,
            "expected_columns": IMPORT_COLUMNS,
        },
    )
