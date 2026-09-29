"""
User uploads and generated exports must land in git-ignored directories, so
they can never be committed to this (public) repository.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db.models import FileField
from django.test import SimpleTestCase, override_settings

REPO_ROOT = Path(settings.BASE_DIR).parent


def is_git_ignored(path):
    result = subprocess.run(
        ['git', 'check-ignore', '-q', '--no-index', str(path)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f'git check-ignore failed: {result.stderr}')
    return result.returncode == 0


def upload_dirs():
    """Every static upload_to prefix declared by a FileField/ImageField."""
    dirs = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, FileField) and isinstance(field.upload_to, str):
                dirs.add(field.upload_to)
    return sorted(dirs)


class StoragePathsAreIgnoredTest(SimpleTestCase):

    def test_upload_inventory_is_not_empty(self):
        self.assertIn('resumes/', upload_dirs())
        self.assertIn('avatars/', upload_dirs())

    def test_media_root_is_ignored(self):
        self.assertTrue(is_git_ignored(Path(settings.MEDIA_ROOT) / 'probe.upload'))

    def test_every_upload_dir_is_ignored(self):
        for upload_to in upload_dirs():
            with self.subTest(upload_to=upload_to):
                # Neutral extension: the directory rule must match, not a *.pdf/*.png rule.
                path = Path(settings.MEDIA_ROOT) / upload_to / 'probe.upload'
                self.assertTrue(is_git_ignored(path), f'{path} would be committable')

    def test_exports_dir_is_ignored(self):
        self.assertTrue(is_git_ignored(Path(settings.MEDIA_ROOT) / 'exports' / 'export_1_users.upload'))

    def test_static_root_is_ignored(self):
        self.assertTrue(is_git_ignored(Path(settings.STATIC_ROOT) / 'probe.css'))

    def test_export_writer_stays_under_media_root(self):
        from adminpanel.export_utils import write_export_file
        media_root = tempfile.mkdtemp(prefix='test-media-')
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            path, _size = write_export_file('users', [{'id': 1}], export_id=1)
        written = Path(path).resolve()
        self.assertTrue(str(written).startswith(str(Path(media_root).resolve())), written)
