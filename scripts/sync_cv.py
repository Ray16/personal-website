#!/usr/bin/env python3
"""Download a compiled CV from an explicitly configured HTTPS PDF URL."""
from io import BytesIO
import os
from pathlib import Path
import re
import tempfile
from pypdf import PdfReader
from publications import ROOT, fetch


def validate_pdf(content):
    if not content.startswith(b'%PDF-'):
        raise ValueError('CV source did not return a PDF; keeping the existing CV')
    reader=PdfReader(BytesIO(content),strict=True)
    if reader.is_encrypted or not 1<=len(reader.pages)<=30:
        raise ValueError('CV is encrypted or has an unexpected page count')
    text=' '.join((page.extract_text() or '') for page in reader.pages[:2])
    compact=re.sub(r'\s+',' ',text).lower()
    if 'zhu' not in compact or 'rzhu16@uchicago.edu' not in compact or 'education' not in compact:
        raise ValueError('Downloaded PDF does not match Ray Zhu’s CV')
    return len(reader.pages)


def synchronize(url,target=None,loader=fetch):
    target=target or ROOT/'assets/pdfs/Resume.pdf'
    content=loader(url)
    pages=validate_pdf(content)
    if target.exists() and target.read_bytes()==content:
        return False,pages
    with tempfile.NamedTemporaryFile(dir=target.parent,suffix='.pdf',delete=False) as temp:
        temp.write(content)
        path=Path(temp.name)
    path.replace(target)
    return True,pages


def main():
    url=os.environ.get('OVERLEAF_CV_PDF_URL','').strip()
    if not url:
        print('CV sync not configured: an accessible compiled-PDF URL is still needed. Existing CV retained.')
        return
    changed,pages=synchronize(url)
    print(f'CV {"updated" if changed else "unchanged"}: {pages} validated pages.')

if __name__=='__main__':
    main()
