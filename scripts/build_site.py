#!/usr/bin/env python3
"""Stage only public website files for GitHub Pages."""
from pathlib import Path
import shutil
from check_site import PAGES, ROOT, check

check()
output = ROOT / 'dist'
if output.exists():
    shutil.rmtree(output)
output.mkdir()
for name in (*PAGES, 'styles.css', 'nav.js', 'theme-init.js', 'favicon.svg',
             'CNAME', 'robots.txt', 'sitemap.xml'):
    shutil.copy2(ROOT / name, output / name)
shutil.copytree(ROOT / 'assets', output / 'assets')
print('Public site staged in dist/ (local admin tools and source scripts excluded).')
