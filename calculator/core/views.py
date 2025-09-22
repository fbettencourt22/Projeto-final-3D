import io
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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




def parse_decimal(value):
    """Converte o valor em Decimal, aceitando strings com vírgula."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        raise ValueError("valor em falta")
    value_str = str(value).strip()
    if not value_str:
        raise ValueError("valor em falta")
    value_str = value_str.replace(",", ".")
    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"valor inválido: {value}") from exc





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

    try:
        from openpyxl import Workbook  # type: ignore
    except ImportError:
        messages.error(
            request,
            "Suporte a Excel indisponível (biblioteca openpyxl não instalada).",
        )
        return redirect("pieces_list")

    wb = Workbook()
    ws = wb.active
    ws.title = "Peças"
    headers = [
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
    ws.append(headers)

    for piece in pieces:
        created_at = piece.created_at
        if created_at is not None:
            if timezone.is_aware(created_at):
                created_at = timezone.localtime(created_at)
            created_at = created_at.replace(tzinfo=None)
        ws.append(
            [
                piece.name or "",
                float(piece.filament_price_per_kg),
                float(piece.filament_weight_g),
                float(piece.print_time_hours),
                float(piece.labour_time_minutes),
                float(piece.margin_percentage),
                float(piece.cost_filament),
                float(piece.cost_energy),
                float(piece.cost_labour),
                float(piece.cost_machine),
                float(piece.cost_total),
                float(piece.price_final),
                float(piece.consumption_kwh),
                created_at,
                piece.user.get_username() if piece.user else "",
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="pecas_{timestamp}.xlsx"'

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response.write(buffer.getvalue())
    return response



@login_required
def piece_import_view(request):
    form = PieceImportForm()
    errors: list[str] = []
    created = 0

    numeric_fields = [
        "filament_price_per_kg",
        "filament_weight_g",
        "print_time_hours",
        "labour_time_minutes",
        "margin_percentage",
    ]

    def process_payload(raw_payload, line_no):
        nonlocal created
        cleaned = {
            "piece_name": (raw_payload.get("piece_name") or "").strip(),
        }
        for key in numeric_fields:
            try:
                cleaned[key] = parse_decimal(raw_payload.get(key))
            except ValueError as exc:
                raise ValueError(f"{key}: {exc}") from exc

        if cleaned["margin_percentage"] >= Decimal("100"):
            raise ValueError("Margem deve ser inferior a 100%.")

        result = calculate_print_job(cleaned)

        PrintJob.objects.create(
            user=request.user,
            name=cleaned["piece_name"],
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
        created += 1

    if request.method == "POST":
        form = PieceImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data["file"]
            ext = Path(uploaded.name or "").suffix.lower()

            if ext != ".xlsx":
                errors.append("Formato não suportado. Utilize um ficheiro Excel (.xlsx).")
            else:
                try:
                    from openpyxl import load_workbook  # type: ignore
                except ImportError:
                    errors.append(
                        "Suporte a Excel indisponível (biblioteca openpyxl não instalada)."
                    )
                else:
                    try:
                        uploaded.seek(0)
                        workbook = load_workbook(uploaded, data_only=True)
                        sheet = workbook.active
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"Erro ao ler Excel: {exc}")
                    else:
                        rows = list(sheet.iter_rows(values_only=True))
                        if not rows:
                            errors.append("O ficheiro Excel está vazio.")
                        else:
                            headers = [
                                (str(cell).strip() if cell is not None else "")
                                for cell in rows[0]
                            ]
                            missing = [
                                col for col in IMPORT_COLUMNS if col not in headers
                            ]
                            if missing:
                                errors.append(
                                    "Colunas em falta: " + ", ".join(missing)
                                )
                            else:
                                index_map = {name: headers.index(name) for name in IMPORT_COLUMNS}
                                for row_number, row in enumerate(rows[1:], start=2):
                                    payload = {}
                                    for key, idx in index_map.items():
                                        payload[key] = row[idx] if idx < len(row) else None
                                    try:
                                        process_payload(payload, row_number)
                                    except Exception as exc:  # noqa: BLE001
                                        errors.append(f"Linha {row_number}: {exc}")

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




