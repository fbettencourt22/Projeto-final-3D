import io
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import unicodedata

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from .forms import FilamentTypeForm, InventoryQuantityForm, PieceImportForm, PrintJobForm
from .models import FilamentType, InventoryItem, PrintJob

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




def normalize_text(value: str) -> str:
    if not value:
        return ''
    normalized = unicodedata.normalize('NFKD', value)
    stripped = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.lower()


def parse_decimal(value):
    """Converte o valor em Decimal, aceitando strings com vArgula."""
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
        raise ValueError(f"valor invAlido: {value}") from exc





def piece_permission_check(user, piece: PrintJob):
    if user.is_superuser:
        return True
    return piece.user == user


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    links = [
        {'url': 'calculator', 'label': 'Calculadora', 'description': 'Calculadora de custos de impressao 3D.'},
        {'url': 'pieces_list', 'label': 'Historico de pe\u00e7as', 'description': 'Consulte, edite e exporte os seus calculos anteriores.'},
        {'url': 'piece_import', 'label': 'Importar pe\u00e7as', 'description': 'Carregue um ficheiro Excel para criar pe\u00e7as em massa.'},
        {'url': 'inventory', 'label': 'Inventario', 'description': 'Gerir filamentos e pe\u00e7as disponiveis.'},
    ]
    return render(request, 'core/dashboard.html', {'links': links})


@login_required
def inventory_view(request):
    active_tab = request.GET.get('tab', 'filaments')
    if active_tab not in {'filaments', 'pieces'}:
        active_tab = 'filaments'

    filaments = FilamentType.objects.filter(user=request.user).order_by('name')
    inventory_items_qs = (
        InventoryItem.objects.filter(user=request.user)
        .select_related('print_job')
        .order_by('piece_name')
    )

    pieces_search = request.GET.get('pieces_search', '').strip()
    inventory_items_list = list(inventory_items_qs)

    if pieces_search:
        norm_search = normalize_text(pieces_search)
        inventory_items_list = [
            item
            for item in inventory_items_list
            if norm_search in normalize_text(item.piece_name or '')
            or (item.print_job and norm_search in normalize_text(item.print_job.name or ''))
            or (pieces_search.isdigit() and item.print_job and pieces_search == str(item.print_job.pk))
        ]
        active_tab = 'pieces'

    filament_form = FilamentTypeForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_filament':
            filament_form = FilamentTypeForm(request.POST)
            if filament_form.is_valid():
                filament = filament_form.save(commit=False)
                filament.user = request.user
                filament.save()
                messages.success(request, 'Filamento guardado no inventario.')
                return redirect(f"{reverse('inventory')}?tab=filaments")
        active_tab = 'filaments'

    return render(
        request,
        'core/inventory.html',
        {
            'filament_form': filament_form,
            'filaments': filaments,
            'inventory_items': inventory_items_list,
            'active_tab': active_tab,
            'pieces_search': pieces_search,
        },
    )


@login_required
def inventory_add_piece_view(request, pk):
    piece = get_object_or_404(PrintJob, pk=pk)
    if not piece_permission_check(request.user, piece):
        return HttpResponseForbidden('Not allowed')

    form = InventoryQuantityForm()
    if request.method == 'POST':
        form = InventoryQuantityForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            piece_label = piece.name or f'Pe\u00e7a #{piece.pk}'
            item, created = InventoryItem.objects.get_or_create(
                user=request.user,
                print_job=piece,
                defaults={'quantity': quantity, 'piece_name': piece_label},
            )
            if not created:
                item.quantity += quantity
                item.piece_name = piece_label
                item.save(update_fields=['quantity', 'piece_name', 'updated_at'])
            messages.success(request, 'Pe\u00e7a adicionada ao inventario.')
            return redirect(f"{reverse('inventory')}?tab=pieces")

    return render(
        request,
        'core/inventory_add_piece.html',
        {
            'form': form,
            'piece': piece,
        },
    )


@login_required
def inventory_filament_edit_view(request, pk):
    qs = FilamentType.objects.all() if request.user.is_superuser else FilamentType.objects.filter(user=request.user)
    filament = get_object_or_404(qs, pk=pk)

    form = FilamentTypeForm(instance=filament)
    if request.method == 'POST':
        form = FilamentTypeForm(request.POST, instance=filament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Filamento atualizado.')
            return redirect(f"{reverse('inventory')}?tab=filaments")

    return render(
        request,
        'core/inventory_filament_form.html',
        {
            'form': form,
            'filament': filament,
        },
    )


@login_required
def inventory_filament_delete_view(request, pk):
    qs = FilamentType.objects.all() if request.user.is_superuser else FilamentType.objects.filter(user=request.user)
    filament = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        filament.delete()
        messages.success(request, 'Filamento removido do inventario.')
        return redirect(f"{reverse('inventory')}?tab=filaments")

    return render(
        request,
        'core/inventory_filament_confirm_delete.html',
        {
            'filament': filament,
        },
    )


@login_required
def inventory_item_edit_view(request, pk):
    qs = InventoryItem.objects.select_related('print_job')
    if not request.user.is_superuser:
        qs = qs.filter(user=request.user)
    item = get_object_or_404(qs, pk=pk)

    form = InventoryQuantityForm(initial={'quantity': item.quantity})
    if request.method == 'POST':
        form = InventoryQuantityForm(request.POST)
        if form.is_valid():
            item.quantity = form.cleaned_data['quantity']
            item.save(update_fields=['quantity', 'updated_at'])
            messages.success(request, 'Inventario atualizado.')
            return redirect(f"{reverse('inventory')}?tab=pieces")

    return render(
        request,
        'core/inventory_item_form.html',
        {
            'form': form,
            'item': item,
        },
    )


@login_required
def inventory_item_delete_view(request, pk):
    qs = InventoryItem.objects.all() if request.user.is_superuser else InventoryItem.objects.filter(user=request.user)
    item = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Pe\u00e7a removida do inventario.')
        return redirect(f"{reverse('inventory')}?tab=pieces")

    return render(
        request,
        'core/inventory_item_confirm_delete.html',
        {
            'item': item,
        },
    )


@login_required
def calculator_view(request):
    result = None

    if request.method == "POST":
        form = PrintJobForm(request.POST, user=request.user)
        if form.is_valid():
            cleaned = form.cleaned_data
            filament = cleaned["filament_type"]
            cleaned["filament_price_per_kg"] = filament.price_per_kg
            result = calculate_print_job(cleaned)
            result["filament_name"] = filament.name
            result["filament_color"] = filament.color
            result["filament_price_per_kg"] = to_currency(filament.price_per_kg)

            print_job = PrintJob.objects.create(
                user=request.user,
                name=cleaned.get("piece_name", ""),
                filament_type=filament,
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

            result["piece_name"] = print_job.name or f"Pe\u00e7a #{print_job.pk}"
            result["created_at"] = print_job.created_at

            form = PrintJobForm(user=request.user)
    else:
        form = PrintJobForm(user=request.user)

    pieces_qs = PrintJob.objects.select_related("user")
    if request.user.is_superuser:
        pieces = pieces_qs.exclude(inventory_records__isnull=False).distinct()
    else:
        pieces = (
            pieces_qs
            .filter(user=request.user)
            .exclude(inventory_records__user=request.user)
            .distinct()
        )

    has_filaments = form.fields["filament_type"].queryset.exists()

    context = {
        "form": form,
        "result": result,
        "pieces": pieces,
        "has_filaments": has_filaments,
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
    if request.user.is_superuser:
        base_queryset = pieces_qs.exclude(inventory_records__isnull=False).distinct()
    else:
        base_queryset = (
            pieces_qs
            .filter(user=request.user)
            .exclude(inventory_records__user=request.user)
            .distinct()
        )

    search_query = request.GET.get('search', '').strip()
    queryset = base_queryset
    if search_query:
        filters = Q(name__icontains=search_query)
        if search_query.isdigit():
            filters |= Q(pk=int(search_query))
        queryset = queryset.filter(filters).distinct()

    pieces_list = list(queryset)
    if search_query:
        norm_query = normalize_text(search_query)
        pieces_list = [
            piece
            for piece in pieces_list
            if norm_query in normalize_text(piece.name or '')
            or norm_query in normalize_text(str(piece.pk))
        ]

    context = {"pieces": pieces_list, "search_query": search_query}
    return render(request, "core/pieces_list.html", context)


@login_required
def piece_edit_view(request, pk: int):
    piece = get_object_or_404(PrintJob.objects.select_related("user"), pk=pk)
    if not piece_permission_check(request.user, piece):
        return HttpResponseForbidden("Sem permissao.")

    initial = {
        "piece_name": piece.name,
        "filament_type": piece.filament_type,
        "filament_weight_g": piece.filament_weight_g,
        "print_time_hours": piece.print_time_hours,
        "labour_time_minutes": piece.labour_time_minutes,
        "margin_percentage": piece.margin_percentage,
    }

    if initial["filament_type"] is None:
        filament_qs = FilamentType.objects.all().order_by("name")
        if not request.user.is_superuser:
            filament_qs = filament_qs.filter(user=request.user)
        guess = filament_qs.filter(price_per_kg=piece.filament_price_per_kg).first()
        if guess is not None:
            initial["filament_type"] = guess

    if request.method == "POST":
        form = PrintJobForm(request.POST, user=request.user, existing_piece=piece)
        if form.is_valid():
            cleaned = form.cleaned_data
            filament = cleaned["filament_type"]
            cleaned["filament_price_per_kg"] = filament.price_per_kg
            result = calculate_print_job(cleaned)

            piece.name = cleaned.get("piece_name", "")
            piece.filament_type = filament
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
        form = PrintJobForm(initial=initial, user=request.user, existing_piece=piece)

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
            "Suporte a Excel indisponAvel (biblioteca openpyxl nAo instalada).",
        )
        return redirect("pieces_list")

    wb = Workbook()
    ws = wb.active
    ws.title = "Pe\u00e7as"
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
    ] = f'attachment; filename="pe\u00e7as_{timestamp}.xlsx"'

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
        piece_name = cleaned["piece_name"]
        if piece_name:
            exists_qs = PrintJob.objects.filter(user=request.user, name__iexact=piece_name)
            if exists_qs.exists():
                raise ValueError("Ja existe uma pe\u00e7a com este nome.")
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
                errors.append("Formato nAo suportado. Utilize um ficheiro Excel (.xlsx).")
            else:
                try:
                    from openpyxl import load_workbook  # type: ignore
                except ImportError:
                    errors.append(
                        "Suporte a Excel indisponAvel (biblioteca openpyxl nAo instalada)."
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
                            errors.append("O ficheiro Excel estA vazio.")
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
                    f"Importadas {created} peAa(s) para o seu utilizador.",
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









