from pathlib import Path
lines = Path('calculator/core/forms.py').read_text().splitlines()
for i, line in enumerate(lines[:80]):
    print(i, repr(line))
