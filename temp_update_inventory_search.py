from pathlib import Path
text = Path('calculator/core/views.py').read_text().splitlines()
# Update inventory_view with search
out_lines = []
inside_inventory = False
for line in text:
    if line.strip().startswith('def inventory_view('):
        inside_inventory = True
    if inside_inventory and line.strip().startswith('filament_form = FilamentTypeForm('):
        out_lines.append('    pieces_search = request.GET.get("pieces_search", "").strip()')
        out_lines.append('')
        out_lines.append(line)
        continue
    out_lines.append(line)
    if inside_inventory and line.strip() == 'filament_form = FilamentTypeForm()':
        out_lines.append('')
        out_lines.append('    if pieces_search:')
        out_lines.append('        inventory_items = inventory_items.filter(')
        out_lines.append('            Q(piece_name__icontains=pieces_search) | Q(print_job__name__icontains=pieces_search)')
        out_lines.append('        )')
        out_lines.append('        active_tab = "pieces"')
    if inside_inventory and line.strip().startswith('return render('):
        inside_inventory = False
# Ensure  pieces_search in context
text = '\n'.join(out_lines)
old_context = "        {\n            'filament_form': filament_form,\n            'filaments': filaments,\n            'inventory_items': inventory_items,\n            'active_tab': active_tab,\n        },"
new_context = "        {\n            'filament_form': filament_form,\n            'filaments': filaments,\n            'inventory_items': inventory_items,\n            'active_tab': active_tab,\n            'pieces_search': pieces_search,\n        },"
if old_context not in text:
    raise SystemExit('inventory context block not found')
text = text.replace(old_context, new_context)
Path('calculator/core/views.py').write_text(text + '\n', encoding='utf-8')
