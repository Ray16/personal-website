"""Regression tests for source imports, deduplication, date handling, and safe CV replacement."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from publications import (ROOT, DATA, OVERRIDES, merge_records, parse_profile,
                          parse_detail, render_page, render_records)
from refresh_news import refresh
from refresh_thumbnails import find_image
from sync_cv import validate_pdf, synchronize

FIXTURES=ROOT/'scripts/fixtures'

class ContentTests(unittest.TestCase):
    def setUp(self):
        self.profile=parse_profile((FIXTURES/'scholar-profile.html').read_bytes())
        self.records=json.loads((FIXTURES/'publications.json').read_text())['publications']
        self.overrides=json.loads(OVERRIDES.read_text())

    def test_real_scholar_profile_and_2026_records(self):
        self.assertEqual(17,len(self.profile))
        current=[r for r in self.profile if r['year']==2026]
        self.assertEqual(2,len(current))
        self.assertTrue(any('ModelSEED' in r['title'] for r in current))

    def test_new_paper_is_added_and_reimport_is_idempotent(self):
        old=[r for r in self.records if 'ModelSEED' not in r['title']]
        before=deepcopy(old)
        merged,added=merge_records(old,self.profile,self.overrides,
            lambda url:(FIXTURES/'scholar-modelseed.html').read_bytes())
        self.assertEqual(before,old)
        self.assertEqual(1,len(added))
        self.assertEqual(12,len(merged))
        again,added=merge_records(merged,self.profile,self.overrides)
        self.assertEqual(merged,again)
        self.assertEqual([],added)

    def test_publication_year_correction_preserves_curated_image(self):
        old=deepcopy(self.records)
        cof=next(r for r in old if 'COF-999' in r['title'])
        cof['year']=2025
        cof['thumbnail']={'path':'a-real-image.jpg'}
        merged,_=merge_records(old,self.profile,self.overrides)
        cof=next(r for r in merged if 'COF-999' in r['title'])
        self.assertEqual(2026,cof['year'])
        self.assertEqual({'path':'a-real-image.jpg'},cof['thumbnail'])

    def test_missing_scholar_records_are_not_deleted(self):
        merged,_=merge_records(self.records,self.profile[:2],self.overrides)
        self.assertEqual(12,len(merged))

    def test_blocked_and_wrong_profiles_fail_closed(self):
        for source in [b'<h1>Sign in</h1>',b'<h1>CAPTCHA</h1>',b'<div id="gsc_prf_in">Another Person</div>']:
            with self.assertRaises(ValueError): parse_profile(source)

    def test_preprint_duplicates_and_posters_are_excluded(self):
        merged,_=merge_records(self.records,self.profile,self.overrides)
        self.assertEqual(12,len(merged))
        self.assertFalse(any(r['title']=='Deep Learning for Molecular Orbitals' for r in merged))
        self.assertFalse(any(r['venue'].startswith('Poster:') for r in merged))

    def test_renderer_preserves_template_and_escapes_remote_text(self):
        rendered=render_page(self.records)
        self.assertIn('id="nav-toggle"',rendered)
        self.assertEqual(12,rendered.count('<article class="pub-item">'))
        hostile=deepcopy(self.records[:1]);hostile[0]['title']='<script>alert(1)</script>'
        markup=render_records(hostile)
        self.assertNotIn('<script>',markup)
        self.assertIn('&lt;script&gt;',markup)

    def test_only_paper_images_are_selected(self):
        source=b'<title>Real paper</title><meta property="og:image" content="journal-logo.jpg"><figure><img src="figure1.jpg"></figure>'
        self.assertEqual(('https://journal.example/figure1.jpg','Figure from the paper'),find_image(source,'https://journal.example/article','Real paper'))
        self.assertIsNone(find_image(b'<title>Access denied</title><img src="logo.jpg">','https://journal.example/article','Real paper'))

    def test_past_and_future_events_and_multi_day_end(self):
        raw='<p><time datetime="2026-07-20">July 20-24</time> - I will be attending a school. <a href="https://example.org">Website</a></p>'
        self.assertEqual(raw,refresh(raw,date(2026,7,22)))
        changed=refresh(raw,date(2026,7,25))
        self.assertIn('I attended a school',changed)
        self.assertIn('href="https://example.org"',changed)
        self.assertEqual(changed,refresh(changed,date(2026,11,2)))
        month='<p><time datetime="2025-11">November</time> - I started a position.</p>'
        self.assertEqual(month,refresh(month,date(2026,11,2)))

    def test_bad_cv_download_does_not_replace_the_saved_pdf(self):
        for bad in [b'<html>Log in to Overleaf</html>',b'%PDF-truncated']:
            with self.assertRaises(Exception): validate_pdf(bad)
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'Resume.pdf';path.write_bytes(b'original CV')
                with self.assertRaises(Exception): synchronize('https://example.org/cv.pdf',path,lambda url:bad)
                self.assertEqual(b'original CV',path.read_bytes())

    def test_current_catalog_is_fully_rendered(self):
        current=json.loads(DATA.read_text())['publications']
        self.assertEqual(render_page(current),(ROOT/'publications.html').read_text())

    def test_actual_cv_identity_and_idempotent_refresh(self):
        source=(ROOT/'assets/pdfs/Resume.pdf').read_bytes()
        pages=validate_pdf(source)
        self.assertGreaterEqual(pages,1)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'Resume.pdf'
            self.assertEqual((True,pages),synchronize('https://example.org/cv.pdf',path,lambda url:source))
            self.assertEqual((False,pages),synchronize('https://example.org/cv.pdf',path,lambda url:source))

if __name__=='__main__': unittest.main()
