from pathlib import Path
path = Path('calculator/core/templates/core/calculator.html')
text = path.read_text(encoding='utf-8')
form_marker = '            <div class="tab-pane fade show active" id="tab-calculadora" role="tabpanel" aria-labelledby="calc-tab">\r\n                <form method="post" novalidate class="row g-3">\r\n                    {% csrf_token %}\r\n'
if form_marker not in text:
    raise SystemExit('form marker not found')
replacement = '            <div class="tab-pane fade show active" id="tab-calculadora" role="tabpanel" aria-labelledby="calc-tab">\r\n                {% if not has_filaments %}\r\n                    <div class="alert alert-warning mb-3">Adicione pelo menos um filamento no inventario para utilizar a calculadora.</div>\r\n                {% endif %}\r\n                <form method="post" novalidate class="row g-3">\r\n                    {% csrf_token %}\r\n'
text = text.replace(form_marker, replacement)
path.write_text(text, encoding='utf-8')
