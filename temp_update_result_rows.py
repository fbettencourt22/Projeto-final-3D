from pathlib import Path
path = Path('calculator/core/templates/core/calculator.html')
text = path.read_text()
needle = "                                <tr><th scope=\"row\">Pea</th><td>{{ result.piece_name }}</td></tr>\n                                <tr><th scope=\"row\">Data</th><td>{{ result.created_at|date:\"d/m/Y H:i\" }}</td></tr>\n"
replacement = "                                <tr><th scope=\"row\">Peca</th><td>{{ result.piece_name }}</td></tr>\n                                {% if result.filament_name %}\n                                <tr><th scope=\"row\">Filamento</th><td>{{ result.filament_name }}{% if result.filament_color %} ({{ result.filament_color }}){% endif %}</td></tr>\n                                {% endif %}\n                                {% if result.filament_price_per_kg %}\n                                <tr><th scope=\"row\">Filamento (EUR/kg)</th><td>{{ result.filament_price_per_kg }}</td></tr>\n                                {% endif %}\n                                <tr><th scope=\"row\">Data</th><td>{{ result.created_at|date:\"d/m/Y H:i\" }}</td></tr>\n"
if needle not in text:
    raise SystemExit('needle not found for row replacement')
text = text.replace(needle, replacement)
path.write_text(text)
