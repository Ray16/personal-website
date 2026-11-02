#!/usr/bin/env python3
"""Migrate an existing ignored local editor to the redesigned card markup."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parent.parent
if not (root/'server.py').exists() or not (root/'admin.js').exists():
    print('No existing local admin installation found; nothing to migrate.')
    sys.exit(0)
if 'def _parse_card_entries' in (root/'server.py').read_text() and "holder.querySelector('.project-links')" in (root/'admin.js').read_text():
    admin_path=root/'admin.js'
    admin_source=admin_path.read_text()
    admin_source=admin_source.replace('.poster-body > p:not(.eyebrow)', '.poster-body > p:not(.eyebrow):not(.entry-meta)').replace("holder.querySelector('.eyebrow')", "holder.querySelector('.entry-meta, .eyebrow')")
    admin_source=admin_source.replace(':not(.entry-meta):not(.entry-meta)', ':not(.entry-meta)')
    admin_path.write_text(admin_source)
    print('Local editor already supports the redesigned cards.')
    sys.exit(0)
p=root/'server.py';s=p.read_text()
# Keep the existing local editor compatible with complete card fragments.
s=s.replace('''        elif filename == "project.html":
            for m in re.finditer(r'<h1>(.*?)</h1>', html):
                sections.append(m.group(1))''','''        elif filename == "project.html":
            for m in re.finditer(r'data-admin-section="([^"]+)"', html):
                sections.append(m.group(1))
            if not sections:
                sections = re.findall(r'<h1>(.*?)</h1>', html)''')
needle='''        parser = parsers.get(filename)
        return parser(html) if parser else []'''
replacement='''        if filename in {"project.html", "poster.html", "presentation.html"}:
            cards = self._parse_card_entries(html, filename)
            if cards:
                return cards
        parser = parsers.get(filename)
        return parser(html) if parser else []

    def _parse_card_entries(self, html, filename):
        """Return whole cards so editing or deleting never removes adjacent markup."""
        entries = []
        for match in re.finditer(r'(<article class="(?:project-card|poster-card|talk-card)">.*?</article>)', html, re.DOTALL):
            raw = match.group(1)
            title = re.search(r'<h[23]>(.*?)</h[23]>', raw, re.DOTALL)
            if not title:
                continue
            clean = lambda text: html_unescape(re.sub(r'<[^>]+>', '', text)).strip()
            title_text = clean(title.group(1))
            desc = re.search(r'<p>(.*?)</p>', raw, re.DOTALL)
            links = [{"url": url, "label": clean(label).removesuffix(" ↗")} for url, label in re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', raw, re.DOTALL)]
            if filename == "project.html":
                before = html[:match.start()]
                sections = re.findall(r'data-admin-section="([^"]+)"', before)
                section = sections[-1] if sections else "Research"
                fields = {"description": title_text, "url": links[0]["url"] if links else "", "displayDate": "", "isoDate": ""}
            elif filename == "poster.html":
                section = "Posters"
                fields = {"title": title_text, "description": clean(desc.group(1)) if desc else "", "links": links}
            else:
                section = "Slides"
                fields = {"description": title_text, "url": links[0]["url"] if links else "", "displayDate": "", "isoDate": ""}
            entries.append({"section": section, "summary": title_text, "date": "", "html": raw, "fields": fields})
        return entries'''
assert needle in s;s=s.replace(needle,replacement);p.write_text(s)
p=root/'admin.js';s=p.read_text()
# Preserve established illustrations, descriptive text, and structure during edits.
s=s.replace("        if (page === 'index.html') {\n            var startDate", """        if (state.editingEntry && /<article /.test(state.editingEntry.html)) {
            var holder = document.createElement('div');
            holder.innerHTML = state.editingEntry.html;
            var title = holder.querySelector('h2, h3');
            title.textContent = val(page === 'poster.html' ? 'f-title' : 'f-desc');
            if (!title.textContent.trim()) { toast('Title is required.', 'error'); return null; }
            if (page === 'poster.html') {
                var description = holder.querySelector('.poster-body > p:not(.eyebrow):not(.entry-meta)');
                if (description) description.textContent = val('f-desc');
                var linkBox = holder.querySelector('.project-links');
                if (linkBox) linkBox.innerHTML = getLinks().map(function (l) { return '<a href="' + esc(l.url) + '" target="_blank" rel="noopener">' + esc(l.label) + ' ↗</a>'; }).join('');
            } else {
                var firstLink = holder.querySelector('.project-links a, .talk-card > a');
                var url = val('f-url');
                if (firstLink && url) firstLink.setAttribute('href', url);
                else if (firstLink && !url) firstLink.remove();
                else if (url) {
                    var a = document.createElement('a'); a.href = url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = 'View resource ↗';
                    (holder.querySelector('.project-links') || holder.querySelector('.talk-card')).appendChild(a);
                }
                if (val('f-date-start')) {
                    var date = holder.querySelector('.entry-meta, .eyebrow') || holder.querySelector('.talk-card > p');
                    if (date) date.textContent = formatDisplayDate(val('f-date-start'), val('f-date-end'));
                }
            }
            return holder.innerHTML;
        }
        if (page === 'index.html') {
            var startDate""")
# Wrap new entries into the same card system; old raw forms still supply content.
s=s.replace("        var section = val('f-section');\n\n        if (page === 'index.html')", """        var section = val('f-section');
        if (page === 'project.html' || page === 'poster.html' || page === 'presentation.html') {
            var doc = new DOMParser().parseFromString(html, 'text/html');
            var target;
            if (page === 'project.html') {
                var group = Array.from(doc.querySelectorAll('[data-admin-section]')).find(function (el) { return el.dataset.adminSection === section; });
                if (!group) return null;
                target = group.querySelector('.project-grid, .talk-list');
                snippet = '<article class="talk-card"><h3>' + snippet.replace(/^<p>|<\\/p>$/g, '') + '</h3></article>';
            } else if (page === 'poster.html') {
                target = doc.querySelector('.poster-grid');
                snippet = '<article class="poster-card"><div class="poster-body">' + snippet + '</div></article>';
            } else {
                target = doc.querySelector('.talk-list');
                snippet = '<article class="talk-card">' + snippet.replace('<p>', '<h2>').replace('</p>', '</h2>') + '</article>';
            }
            if (!target) return null;
            target.insertAdjacentHTML('afterbegin', snippet);
            return '<!DOCTYPE html>\\n' + doc.documentElement.outerHTML;
        }

        if (page === 'index.html')""")
s=s.replace("var yearGroupMarker = 'data-year=\"' + yearOrNew + '\"';", "var yearGroupMarker = 'class=\"news-year-group\" data-year=\"' + yearOrNew + '\"';")
p.write_text(s)
