"""
Resume PDF text extraction (both code paths) works with pypdf and does not
need the deprecated PyPDF2 package.
"""

import shutil
import sys
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from ats_signals.models import Resume
from ats_signals.services import legacy_compat
from ats_signals.services.resume_services import ResumeAnalysisService


def make_pdf(pages):
    """A minimal, valid PDF with one text line per page (Helvetica, uncompressed)."""
    objects = []
    n_pages = len(pages)
    font_id = 3 + 2 * n_pages
    kids = ' '.join(f'{3 + 2 * i} 0 R' for i in range(n_pages))
    objects.append('<< /Type /Catalog /Pages 2 0 R >>')
    objects.append(f'<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>')
    for i, text in enumerate(pages):
        content_id = 4 + 2 * i
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
                       f'/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>')
        stream = f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'
        objects.append(f'<< /Length {len(stream)} >>\nstream\n{stream}\nendstream')
    objects.append('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')

    out = b'%PDF-1.4\n'
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f'{number} 0 obj\n{body}\nendobj\n'.encode()
    xref = len(out)
    out += f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode()
    out += ''.join(f'{o:010d} 00000 n \n' for o in offsets).encode()
    out += f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    return out


EXTRACTORS = {
    'legacy_compat': legacy_compat._extract_pdf_text,
    'ResumeAnalysisService': ResumeAnalysisService._extract_pdf_text,
}


class PdfExtractionTest(TestCase):

    def setUp(self):
        media = tempfile.mkdtemp(prefix='test-media-')
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_user(username='pdf', email='pdf@example.com', password='x')

    def resume(self, data, name='cv.pdf'):
        return Resume.objects.create(user=self.user, title='cv', file_size=len(data), file_type='pdf',
                                     file=SimpleUploadedFile(name, data, content_type='application/pdf'))

    def test_extracts_text_from_every_page_without_pypdf2(self):
        resume = self.resume(make_pdf(['Jane Candidate', 'Python Django PostgreSQL']))
        with mock.patch.dict(sys.modules, {'PyPDF2': None}):  # PyPDF2 not importable
            for name, extract in EXTRACTORS.items():
                with self.subTest(extractor=name):
                    text = extract(resume)
                    self.assertIsNotNone(text, f'{name} returned no text')
                    self.assertIn('Jane Candidate', text)
                    self.assertIn('Python Django PostgreSQL', text)

    def test_corrupt_pdf_returns_none(self):
        resume = self.resume(b'%PDF-1.4 this is not a real pdf', name='bad.pdf')
        for name, extract in EXTRACTORS.items():
            with self.subTest(extractor=name):
                self.assertIsNone(extract(resume))
