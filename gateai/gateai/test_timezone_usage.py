"""
Django 5 removed django.utils.timezone.utc. Code that still calls it raises
AttributeError at runtime (for example, the Stripe account.updated webhook).
"""

import ast
from pathlib import Path

import django.utils.timezone
from django.conf import settings
from django.test import SimpleTestCase

SOURCE_ROOT = Path(settings.BASE_DIR)
SKIP_PARTS = {'migrations', 'node_modules', 'venv', '.venv', '__pycache__'}


def django_timezone_utc_uses():
    """(file, line) for every `<name>.utc` where <name> is django.utils.timezone."""
    hits = []
    for path in SOURCE_ROOT.rglob('*.py'):
        if SKIP_PARTS & set(path.parts):
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        aliases = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'django.utils':
                aliases |= {a.asname or a.name for a in node.names if a.name == 'timezone'}
            elif isinstance(node, ast.Import):
                aliases |= {a.asname for a in node.names if a.name == 'django.utils.timezone' and a.asname}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and node.attr == 'utc'
                    and isinstance(node.value, ast.Name) and node.value.id in aliases):
                hits.append(f'{path.relative_to(SOURCE_ROOT)}:{node.lineno}')
    return sorted(hits)


class DjangoTimezoneUtcTest(SimpleTestCase):

    def test_django_timezone_has_no_utc(self):
        # Pins the premise: if this ever fails, the check below is moot.
        self.assertFalse(hasattr(django.utils.timezone, 'utc'))

    def test_no_code_uses_django_timezone_utc(self):
        self.assertEqual(django_timezone_utc_uses(), [])
