from pathlib import Path
text = Path('calculator/core/templates/core/dashboard.html').read_text(encoding='utf-8')
segment = text.split('Dashboard',1)[1]
print(repr(segment.splitlines()[0:4]))
