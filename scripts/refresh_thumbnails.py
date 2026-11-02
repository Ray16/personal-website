#!/usr/bin/env python3
"""Download paper-provided TOC images or figures. Never synthesize replacement artwork."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
from PIL import Image
from publications import DATA, ROOT, fetch, same_title, soup_for


def find_image(content, page_url, expected_title):
    soup=soup_for(content)
    meta=soup.select_one('meta[name="citation_title"]')
    title=meta.get('content','') if meta else (soup.title.get_text(' ',strip=True) if soup.title else '')
    # A challenge page or a journal home page must never become a publication thumbnail.
    if not same_title(title,expected_title) and expected_title.lower() not in title.lower():
        return None
    for image in soup.select('img'):
        description=' '.join([str(image.get('alt','')),str(image.get('class',''))]).lower()
        if any(term in description for term in ('graphical abstract','graphical-abstract','toc graphic','table of contents graphic')):
            source=image.get('data-src') or image.get('src')
            if source:
                return urljoin(page_url,source),'TOC graphic from the paper'
    for image in soup.select('figure img'):
        source=image.get('data-src') or image.get('src')
        if source:
            return urljoin(page_url,source),'Figure from the paper'
    return None


def download_thumbnail(record):
    url=record.get('url','')
    if not url.startswith('https://') or urlsplit(url).hostname in {'scholar.google.com'}:
        return None
    candidate=find_image(fetch(url),url,record['title'])
    if not candidate:
        return None
    source,label=candidate
    raw=fetch(source)
    image=Image.open(BytesIO(raw))
    image.load()
    if min(image.size)<120:
        return None
    # Resize the publisher's image only. Do not crop, redraw, or add content.
    image.thumbnail((1000,1000))
    if image.mode=='RGBA':
        background=Image.new('RGB',image.size,'white')
        background.paste(image,mask=image.getchannel('A'))
        image=background
    else:
        image=image.convert('RGB')
    identifier=record.get('scholar_id',record['title']).split(':')[-1]
    filename=re.sub(r'[^A-Za-z0-9_-]','',identifier)+'.jpg'
    target=ROOT/'assets/pubs'/filename
    image.save(target,quality=90)
    return {'path':str(target.relative_to(ROOT)),'source_page':url,'source_url':source,'label':label}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=3,help='Maximum missing figures to attempt per run')
    args=parser.parse_args()
    data=json.loads(DATA.read_text())
    attempts=changed=0
    for record in data['publications']:
        if record.get('thumbnail') or record.get('kind')=='abstract':
            continue
        if attempts>=args.limit:
            break
        attempts+=1
        try:
            thumbnail=download_thumbnail(record)
            if thumbnail:
                record['thumbnail']=thumbnail
                changed+=1
                print('Downloaded original paper image: '+record['title'])
            else:
                print('No verified TOC/figure exposed: '+record['title'])
        except Exception as error:
            print(f'Image source unavailable for {record["title"]}: {type(error).__name__}')
    if changed:
        DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f'Original paper images added: {changed}')

if __name__=='__main__':
    main()
