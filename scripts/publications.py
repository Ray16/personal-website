#!/usr/bin/env python3
"""Import public Google Scholar records and render the publication list without generated prose."""
import argparse
from copy import deepcopy
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data/publications.json'
OVERRIDES = ROOT / 'data/publication-overrides.json'
PROFILE_ID = '3KJaM3sAAAAJ'
PROFILE_URL = f'https://scholar.google.com/citations?user={PROFILE_ID}&hl=en&sortby=pubdate&cstart=0&pagesize=100'
START = '<!-- publications:start -->'
END = '<!-- publications:end -->'


def fetch(url):
    if urlsplit(url).scheme != 'https':
        raise ValueError('Publication sources must use HTTPS')
    request = Request(url, headers={'User-Agent': 'RayZhuWebsite/1.0 (+https://www.ruijiezhu.us)'})
    with urlopen(request, timeout=25) as response:
        content = response.read(15_000_001)
        if len(content) > 15_000_000:
            raise ValueError('Source exceeds size limit')
        return content


def soup_for(content):
    # Scholar declares ISO-8859-1; let BeautifulSoup honor the source declaration.
    return BeautifulSoup(content, 'html.parser')


def parse_profile(content):
    soup = soup_for(content)
    identity = soup.select_one('#gsc_prf_in')
    if not identity or identity.get_text(' ', strip=True) != 'Ruijie Zhu':
        raise ValueError('Scholar profile identity is missing or changed; no update was made')
    rows = soup.select('tr.gsc_a_tr')
    if not rows:
        raise ValueError('Scholar returned no publication rows; it may have blocked the request')
    more = soup.select_one('#gsc_bpf_more')
    if more and not more.has_attr('disabled'):
        raise ValueError('Scholar profile has more than 100 records; pagination needs review')
    records = []
    seen = set()
    for row in rows:
        title = row.select_one('a.gsc_a_at')
        year = row.select_one('.gsc_a_y')
        details = row.select('.gsc_a_t .gs_gray')
        if not title or not year or len(details) < 2:
            raise ValueError('Unrecognized Scholar row; no update was made')
        year_text = year.get_text(strip=True)
        if not re.fullmatch(r'\d{4}', year_text):
            raise ValueError('Publication year is missing; review Scholar before importing')
        scholar_url = urljoin('https://scholar.google.com', title['href'])
        citation = parse_qs(urlsplit(scholar_url).query).get('citation_for_view', [''])[0]
        if not citation.startswith(PROFILE_ID + ':') or citation in seen:
            raise ValueError('Unexpected or duplicated Scholar citation ID')
        seen.add(citation)
        venue_node = deepcopy(details[1])
        # Scholar repeats the year inside a nested span; the year column is authoritative.
        for span in venue_node.select('.gs_oph'):
            span.decompose()
        venue = re.sub(r',?\s*' + year_text + r'\s*$', '', venue_node.get_text(' ', strip=True)).strip()
        records.append({'scholar_id': citation, 'scholar_url': scholar_url,
                        'title': title.get_text(' ', strip=True),
                        'authors': details[0].get_text(' ', strip=True),
                        'venue': venue, 'year': int(year_text)})
    return records


def parse_detail(content):
    soup = soup_for(content)
    link = soup.select_one('#gsc_oci_title a')
    if not link or not link.get('href', '').startswith('https://'):
        raise ValueError('Scholar citation did not provide a public paper link')
    fields = {}
    for row in soup.select('.gs_scl'):
        label, value = row.select_one('.gsc_oci_field'), row.select_one('.gsc_oci_value')
        if label and value:
            fields[label.get_text(' ', strip=True)] = value.get_text(' ', strip=True)
    return {'url': link['href'], 'full_authors': fields.get('Authors', '')}


def normalize(title):
    return re.sub(r'[^a-z0-9]', '', title.lower())


def same_title(a, b):
    a, b = normalize(a), normalize(b)
    return a == b or (min(len(a), len(b)) > 70 and (a.startswith(b) or b.startswith(a)))


def merge_records(existing, incoming, overrides, detail_loader=None):
    """Update only source-backed metadata. Preserve curated links and images; never silently delete."""
    result = deepcopy(existing)
    excluded = overrides.get('exclude', {})
    record_overrides = overrides.get('records', {})
    added = []
    for record in incoming:
        sid = record['scholar_id']
        if sid in excluded or record['venue'].lower().startswith('poster:'):
            continue
        matches = [entry for entry in result if entry.get('scholar_id') == sid or same_title(entry['title'], record['title'])]
        if len(matches) > 1:
            raise ValueError('Ambiguous publication match: ' + record['title'])
        if matches:
            entry = matches[0]
            # Keep the complete author list from the existing record when Scholar truncates it.
            update = {key: value for key,value in record.items() if key != 'authors' or '...' not in value and '…' not in value}
            entry.update(update)
        else:
            entry = deepcopy(record)
            entry['url'] = record['scholar_url']
            if detail_loader:
                try:
                    detail = parse_detail(detail_loader(record['scholar_url']))
                    entry['url'] = detail['url']
                    if detail['full_authors']:
                        entry['authors'] = detail['full_authors']
                except Exception as error:
                    print(f'Paper link unavailable; retaining the Scholar citation link: {type(error).__name__}',file=sys.stderr)
            result.append(entry)
            added.append(entry['title'])
        entry.update(record_overrides.get(sid, {}))
        if not entry.get('kind'):
            venue = entry['venue'].lower()
            entry['kind'] = 'preprint' if any(word in venue for word in ('arxiv', 'biorxiv', 'chemrxiv')) else 'abstract' if 'abstracts' in venue else 'article'
    ids = [entry.get('scholar_id') for entry in result if entry.get('scholar_id')]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate publication IDs after synchronization')
    return sorted(result, key=lambda entry: (-entry['year'], entry['title'].casefold())), added


def authors_html(text):
    parts = re.split(r'(\b(?:R Zhu|Ruijie Zhu|Ray Zhu)\b)', text)
    return ''.join('<strong>' + escape(part) + '</strong>' if part in {'R Zhu','Ruijie Zhu','Ray Zhu'} else escape(part) for part in parts)


def render_records(records):
    lines=[]
    year=None
    for entry in sorted(records,key=lambda e:(-e['year'],e['title'].casefold())):
        if year != entry['year']:
            year=entry['year']
            lines.append(f'            <h2 class="pub-year-heading">{year}</h2>')
        lines.append('            <article class="pub-item">')
        thumb=entry.get('thumbnail')
        if thumb and (ROOT/thumb['path']).is_file():
            lines.extend([
                '                <figure class="pub-thumb">',
                f'                    <a href="{escape(thumb["source_page"],quote=True)}" target="_blank" rel="noopener"><img src="{escape(thumb["path"],quote=True)}" alt="{escape(thumb["label"],quote=True)}" loading="lazy" width="320" height="240"></a>',
                f'                    <figcaption>{escape(thumb["label"])}</figcaption>',
                '                </figure>'])
        url = entry.get('url',entry.get('scholar_url',''))
        if urlsplit(url).scheme != 'https':
            raise ValueError('Unsafe publication URL')
        tag = f' <span class="pub-tag">{escape(entry["kind"])}</span>' if entry.get('kind') in {'preprint','abstract'} else ''
        lines.extend([
            '                <div class="pub-body">',
            f'                    <h3 class="pub-title"><a href="{escape(url,quote=True)}" target="_blank" rel="noopener">{escape(entry["title"])}</a></h3>',
            f'                    <p class="pub-authors">{authors_html(entry["authors"])}</p>',
            f'                    <p class="pub-meta">{escape(entry["venue"])} · {year}{tag}</p>',
            '                </div>',
            '            </article>'])
    return '\n'.join(lines)+'\n'


def render_page(records):
    path=ROOT/'publications.html'
    source=path.read_text()
    if START not in source or END not in source:
        raise ValueError('Publication template markers are missing')
    before,rest=source.split(START,1)
    _,after=rest.split(END,1)
    return before+START+'\n'+render_records(records)+'            '+END+after


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile-file',type=Path,help='Use a saved public Scholar response for reproducible imports')
    parser.add_argument('--render-only',action='store_true')
    args=parser.parse_args()
    data=json.loads(DATA.read_text())
    if args.render_only:
        (ROOT/'publications.html').write_text(render_page(data['publications']))
        return
    content=args.profile_file.read_bytes() if args.profile_file else fetch(PROFILE_URL)
    incoming=parse_profile(content)
    overrides=json.loads(OVERRIDES.read_text())
    records,added=merge_records(data['publications'],incoming,overrides,fetch)
    # Render successfully before writing either file. A blocked/changed source never empties the site.
    rendered=render_page(records)
    payload={**data,'publications':records}
    if records != data['publications']:
        payload['updated_from_scholar']=date.today().isoformat()
        DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'publications.html').write_text(rendered)
    print(f'Scholar sync: {len(incoming)} source records; {len(records)} displayed papers; {len(added)} additions.')
    for title in added: print('Added: '+title)

if __name__=='__main__':
    main()
