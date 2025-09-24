import re
from pathlib import Path

path = Path(r"c:\\Users\\fsbet\\Documents\\GitHub\\Projeto-final-3D-\\calculator\\core\\views.py")
text = path.read_text(encoding="utf-8")

patterns = [
    (
        r"@login_required\ndef inventory_filament_delete_view\(request, pk\):\n(?:    .+\n)+?\n(?=@login_required)",
        """@login_required\ndef inventory_filament_delete_view(request, pk):\n    qs = (\n        FilamentType.objects.all()\n        if request.user.is_superuser\n        else FilamentType.objects.filter(user=request.user)\n    )\n    filament = get_object_or_404(qs, pk=pk)\n\n    fallback = f\"{reverse('inventory')}?tab=filaments\"\n    target = resolve_next_url(request, fallback)\n    if request.method != \"POST\":\n        return redirect(target)\n\n    label = get_filament_label(filament)\n    filament.delete()\n    messages.success(request, f'Filamento \"{label}\" removido do inventario.')\n    return redirect(target)\n\n""",
    ),
    (
        r"@login_required\ndef inventory_item_delete_view\(request, pk\):\n(?:    .+\n)+?\n(?=@login_required)",
        """@login_required\ndef inventory_item_delete_view(request, pk):\n    qs = (\n        InventoryItem.objects.all()\n        if request.user.is_superuser\n        else InventoryItem.objects.filter(user=request.user)\n    )\n    item = get_object_or_404(qs, pk=pk)\n\n    fallback = f\"{reverse('inventory')}?tab=pieces\"\n    target = resolve_next_url(request, fallback)\n    if request.method != \"POST\":\n        return redirect(target)\n\n    label = item.piece_name or f\"Peca #{item.pk}\"\n    item.delete()\n    messages.success(request, f'Peca \"{label}\" removida do inventario.')\n    return redirect(target)\n\n""",
    ),
    (
        r"@login_required\ndef piece_delete_view\(request, pk: int\):\n(?:    .+\n)+?\n(?=@login_required)",
        """@login_required\ndef piece_delete_view(request, pk: int):\n    piece = get_object_or_404(PrintJob.objects.select_related(\"user\"), pk=pk)\n    if not piece_permission_check(request.user, piece):\n        return HttpResponseForbidden(\"Sem permissao.\")\n\n    fallback = reverse('pieces_list')\n    target = resolve_next_url(request, fallback)\n    if request.method != \"POST\":\n        return redirect(target)\n\n    label = piece.name or f\"Peca #{piece.pk}\"\n    piece.delete()\n    messages.success(request, f'Peca \"{label}\" removida.')\n    return redirect(target)\n\n""",
    ),
]

for pattern, replacement in patterns:
    new_text, count = re.subn(pattern, replacement, text, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"Pattern not replaced: {pattern[:40]}...")
    text = new_text

path.write_text(text, encoding="utf-8")
