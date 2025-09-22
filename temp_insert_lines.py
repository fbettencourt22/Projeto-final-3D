from pathlib import Path
lines = Path('calculator/core/forms.py').read_text().splitlines()
lines.insert(63, '        existing_piece = kwargs.pop("existing_piece", None)')
lines.insert(65, '        self.user = user')
lines.insert(66, '        self.existing_piece = existing_piece')
Path('calculator/core/forms.py').write_text('\n'.join(lines) + '\n', encoding='utf-8')
