#!/usr/bin/env python3
"""Validate the public site's local links, assets, document structure, and archive."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

ROOT = Path(__file__).resolve().parent.parent
PAGES = ('index.html', 'publications.html', 'project.html', 'poster.html',
         'presentation.html', 'hobby.html', 'link.html', 'resume.html')

class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids, self.refs, self.headings, self.errors = [], [], [], []
        self.tags, self.stack = Counter(), []
        self.feed(source)
        if self.stack:
            self.errors.append(f'unclosed tags: {self.stack}')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] += 1
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append(tag)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag in {'h1','h2','h3'}:
            self.headings.append(tag)
        for key in ('href', 'src'):
            if attrs.get(key):
                self.refs.append(attrs[key])
        if attrs.get('srcset'):
            self.refs.extend(entry.strip().split()[0] for entry in attrs['srcset'].split(','))
        if tag == 'img' and 'alt' not in attrs:
            self.errors.append('image is missing alt text')
        if tag == 'a' and attrs.get('target') == '_blank' and 'noopener' not in attrs.get('rel',''):
            self.errors.append('external tab link is missing rel=noopener')

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f'unexpected closing tag: {tag}; open: {self.stack[-3:]}')
        else:
            self.stack.pop()


def check():
    docs = {name: Document((ROOT/name).read_text()) for name in PAGES}
    errors = []
    for name, doc in docs.items():
        errors.extend(f'{name}: {error}' for error in doc.errors)
        for tag in ('html','head','body','main','h1','header','footer'):
            if doc.tags[tag] != 1:
                errors.append(f'{name}: expected one {tag}, got {doc.tags[tag]}')
        duplicates = [key for key,count in Counter(doc.ids).items() if count>1]
        if duplicates:
            errors.append(f'{name}: duplicate IDs {duplicates}')
        for ref in doc.refs:
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc:
                continue
            path = unquote(parsed.path) or name
            if not (ROOT/path).is_file():
                errors.append(f'{name}: missing local target {ref}')
            if parsed.fragment and path in docs and parsed.fragment not in docs[path].ids:
                errors.append(f'{name}: missing fragment {ref}')
        for required in ('nav-links','nav-toggle','theme-toggle','main-content'):
            if required not in doc.ids:
                errors.append(f'{name}: missing shared interface {required}')
    news=(ROOT/'index.html').read_text()
    groups=re.findall(r'<div class="news-year-group" data-year="(\d{4})">(.*?)</div>', news, re.S)
    count=0
    for year,body in groups:
        dates=re.findall(r'<time datetime="([^"]+)">',body)
        count+=len(dates)
        if dates != sorted(dates,reverse=True):
            errors.append(f'news in {year} is not newest first')
    if count < 120:
        errors.append(f'archive appears incomplete: {count} entries')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(docs)} public pages, local links/assets, HTML structure, and {count} archived news entries')

if __name__ == '__main__':
    check()
