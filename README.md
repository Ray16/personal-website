# Ray Zhu's personal website

Public site: https://www.ruijiezhu.us  
Source: https://github.com/Ray16/personal-website

A buildless academic portfolio using HTML, CSS, and small JavaScript enhancements. Existing page URLs remain stable. The homepage shows six recent updates, with a complete year-filtered archive; without JavaScript, the full archive and navigation remain accessible.

## Local preview

From this directory:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765. No package installation is needed to serve the website.

## Editing

- `index.html`: introduction, research areas, selected work, news archive, and career history.
- `publications.html`: publication records and available publisher figures. Use a venue label when a real thumbnail is unavailable; do not reference nonexistent image files.
- `project.html`: illustrated project cards and hackathons.
- `poster.html` and `presentation.html`: a shared Talks & Posters section, preserving both original URLs. Schematic illustrations are explicitly identified as topic illustrations, not actual poster previews.
- `hobby.html`, `link.html`, and `resume.html`: personal interests, curated resources, and the existing CV PDF.
- `styles.css`: shared design tokens, typography, layout, responsive rules, and reduced-motion/print styles.
- `theme-init.js`: applies the saved or system theme before the page paints.
- `nav.js`: navigation, theme selection, news filtering, and back-to-top behavior.

Keep news groups in newest-first order. Each group uses `class="news-year-group" data-year="YYYY"`, and each update starts with a `<time datetime="YYYY-MM-DD">` element. Add a matching year button when adding a new year. The Latest view picks the six newest dates automatically.

Local admin files are intentionally ignored by Git, as in the original setup. They are not part of the public deployment. Their local card parsers were updated with this redesign; the news group format remains compatible. On another checkout with an existing local editor, run `python3 scripts/upgrade_local_admin.py` to apply the same compatibility update.

## Validation

```sh
python3 scripts/check_site.py
node --check nav.js
node --check theme-init.js
python3 scripts/build_site.py
```

`build_site.py` stages an explicit list of public files into `dist/`. Admin tools, source scripts, and repository files stay out of the deployed artifact.

For browser checks, install the pinned optional dependency in a virtual environment, install Chromium, and keep the local preview running:

```sh
python -m pip install -r scripts/browser-requirements.txt
python -m playwright install chromium
python scripts/check_browser.py --screenshots /tmp/ray-site-review
```

An existing Chrome can be selected with `--browser-executable "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`. Tests cover all eight pages at six viewport widths, broken images, menu behavior, news filters, theme persistence, reduced motion, disabled JavaScript, and blocked browser storage.

GitHub Actions runs these checks for pull requests and updates to `main`. Successful updates to `main` deploy automatically through GitHub Pages. Browser screenshots are retained as workflow artifacts for 14 days.

## Version control and recovery

The pre-redesign versions remain available:

- Original published version: `5c5db54`.
- Saved local version before redesign: `3f05703` on `backup/before-design-review-2026-11-01`.

Work on a feature branch, inspect the changes, and merge the reviewed version into `main`. To undo a published change while preserving history:

```sh
git switch main
git pull --ff-only
git revert <commit-to-undo>
git push origin main
```

GitHub Pages will publish the reverted version after its checks pass. Do not force-push or reset shared history to perform a rollback.
