from pathlib import Path
path = Path('calculator/core/templates/core/pieces_list.html')
text = path.read_text(encoding='utf-8')
old = "                                        <div class=\"d-flex gap-2\">\r\n                                            <a class=\"btn btn-sm btn-outline-primary\" href=\"{% url 'piece_edit' piece.pk %}\">Editar</a>\r\n                                            <a class=\"btn btn-sm btn-outline-danger\" href=\"{% url 'piece_delete' piece.pk %}\">Apagar</a>\r\n                                        </div>\r\n"
new = "                                        <div class=\"d-flex gap-2\">\r\n                                            <a class=\"btn btn-sm btn-outline-success\" href=\"{% url 'inventory_add_piece' piece.pk %}\">Enviar para inventario</a>\r\n                                            <a class=\"btn btn-sm btn-outline-primary\" href=\"{% url 'piece_edit' piece.pk %}\">Editar</a>\r\n                                            <a class=\"btn btn-sm btn-outline-danger\" href=\"{% url 'piece_delete' piece.pk %}\">Apagar</a>\r\n                                        </div>\r\n"
if old not in text:
    raise SystemExit('expected block not found')
text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
