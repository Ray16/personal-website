# Ray Zhu's personal website

Live website: https://www.ruijiezhu.us
GitHub: https://github.com/Ray16/personal-website

A static academic homepage with larger text, a light default theme, and optional dark mode. Existing page URLs remain stable. The portrait uses its original proportions. Email is visible and can be copied when a mail application is unavailable.

## Content and sources

- `index.html`: biography, selected papers, dated news, and experience. Recent experience was checked against the CV compiled on October 16, 2026.
- `data/publications.json`: source-backed publication metadata and image provenance. The list includes the 2026 ModelSEED preprint and the COF-999 JACS article under its Scholar publication year.
- `data/publication-overrides.json`: canonical links and explicit exclusions for preprints superseded by published papers. Posters are listed on the poster page.
- `publications.html`: the shared page shell plus the generated list between `publications:start` and `publications:end` markers. Edit metadata in the JSON, then run `scripts/publications.py --render-only`.
- `project.html`: current enzyme-design work, EnzymeAI, and earlier projects. Images are used only where an actual paper image is available; no synthesized thumbnails or filler artwork are used.
- `poster.html` and `presentation.html`: poster and presentation records, including the 2026 school and NRT meeting. No poster image is invented when the original is unavailable.
- `hobby.html` and `link.html`: personal interests and resources.
- `assets/pdfs/Resume.pdf`: the latest local compiled CV found during the update, compiled October 16, 2026. It is not being represented as a live Overleaf connection.

Paper images retain the original content and are only resized for display. Their source page, image/archive URL, and figure label are retained with each publication. TOC graphics are preferred when accessible; ordinary paper figures are labeled as figures. Unavailable images are omitted.

## Automatic updates

The public Scholar profile is accessible from the user’s computer but returned HTTP 403 to GitHub’s runner during the first real test. Scholar synchronization therefore runs locally rather than pretending the cloud check succeeded.

`scripts/local_update.py` runs daily at **10:15 local time** through the macOS LaunchAgent `us.ruijiezhu.website-scholar-sync`. It clones a temporary isolated checkout, reads Scholar, validates the identity, merges source-backed records, attempts actual paper images for new content, runs the content checks, and pushes only generated content changes. The regular GitHub deployment workflow then validates and publishes them. It does not commit or overwrite work in the user’s active checkout.

The computer needs to be awake and online, with the existing GitHub credential available. A missed calendar run is normally coalesced by launchd when the computer wakes. Logs are in `~/Library/Logs/PersonalWebsiteSync.log`. The installed schedule points to this checkout and its existing `.venv-scrape` environment; moving either requires updating the schedule. To test read access without writes, run `.venv-scrape/bin/python scripts/local_update.py --check`.

`.github/workflows/update-content.yml` independently runs daily at 10:23 UTC. It updates explicit attendance/presentation wording after the event ends, refreshes the compiled CV when its source has been configured, validates changes, commits them, and dispatches deployment. Cloud Scholar reads remain opt-in through the repository variable `SCHOLAR_SYNC_ON_GITHUB=true`; they are disabled by default because the runner was blocked in testing.

Source failures never erase existing papers or the saved CV. Missing images are omitted rather than invented. Exclusions in `data/publication-overrides.json` keep superseded preprints and separately listed posters out of the main paper list.

For news, same-month and cross-month date ranges are supported. A `data-end-date` on a time element can specify an exact end date. Only explicit attendance/presentation phrases are changed; the updater does not rewrite arbitrary biography text or infer new jobs.

The cloud workflow explicitly dispatches deployment because pushes made with `GITHUB_TOKEN` do not trigger push workflows. GitHub allows `workflow_dispatch` from that token: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow.

### Overleaf CV configuration — still pending

Requested source project: https://www.overleaf.com/project/63d321d7517db7dd0042fa1f.

The project editor URL returned an access error. A read-only share link or accessible compiled-PDF URL is still needed to verify and finish the Overleaf connection. No account password or session cookie is stored in this repository.

Once a stable compiled-PDF URL has been verified, store it as the repository Actions secret `OVERLEAF_CV_PDF_URL`. The updater validates the PDF structure, page count, name, email address, and education section before atomically replacing the saved CV. A login page, expired download, wrong document, or corrupted PDF leaves the saved CV intact. Keep token-bearing URLs in the secret rather than committing them to source.

## Local preview and validation

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765. Serving the website needs no dependencies.

For source import and regression tests, install the pinned requirements in a virtual environment:

```sh
python -m pip install -r scripts/publication-requirements.txt -r scripts/browser-requirements.txt
python -m playwright install chromium
python -m unittest discover -s scripts -p 'test_content.py'
python scripts/check_site.py
node --check nav.js
node --check theme-init.js
python scripts/check_browser.py --screenshots /tmp/ray-site-review
```

Keep the preview server running for browser checks. An existing Chrome can be selected with `--browser-executable "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`. Tests cover all eight pages at six viewport widths, original image loading, navigation, news filters, light default/dark selection, email-copy success and fallback, portrait proportions, reduced motion, and unavailable browser storage.

`python scripts/build_site.py` stages an explicit set of public files in `dist/`. Local admin files, scripts, fixtures, and repository metadata are excluded from deployment. GitHub Actions runs the content, structure, syntax, and browser checks before publishing. Review screenshots remain available as workflow artifacts for 14 days.

Local admin files remain ignored, matching the original setup. `python scripts/upgrade_local_admin.py` updates an existing local editor to support complete article fragments.

## Publishing and rollback

The user has requested completed changes be pushed to `main` so they can review the live site. Do not leave finished site edits local or force-push shared history.

Restore points:

- `5c5db54`: originally published version.
- `3f05703` on `backup/before-design-review-2026-11-01`: saved local version before changes.
- `d517882`: the first redesign.
- `0496441`: the plain academic revision with larger text and the 2026 publications.

Undo a published commit with `git revert <commit>` and push the resulting commit to `main`. GitHub Pages publishes the reverted version after validation passes.
