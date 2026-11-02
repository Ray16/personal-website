#!/usr/bin/env python3
"""Use dated event entries to update explicit attendance wording after an event ends."""
import calendar
from datetime import date,datetime
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
PAST_FORMS={
    'I will be attending ': 'I attended ',
    'I plan to attend ': 'I attended ',
    'I planned to attend ': 'I attended ',
    'I will attend ': 'I attended ',
    'I am attending ': 'I attended ',
    'I will be presenting ': 'I presented ',
    'I will present ': 'I presented ',
}


def event_end(time):
    value=time['datetime']
    if re.fullmatch(r'\d{4}-\d{2}',value):
        year,month=map(int,value.split('-'))
        return date(year,month,calendar.monthrange(year,month)[1])
    start=date.fromisoformat(value)
    if time.get('data-end-date'):
        return date.fromisoformat(time['data-end-date'])
    label=time.get_text(' ',strip=True)
    same_month=re.fullmatch(r'[A-Za-z]+\s+\d+\s*[-–]\s*(\d+)',label)
    if same_month:
        end=start.replace(day=int(same_month.group(1)))
        if end>=start:
            return end
    cross_month=re.fullmatch(r'[A-Za-z]+\s+\d+\s*[-–]\s*([A-Za-z]+)\s+(\d+)',label)
    if cross_month:
        months={name.lower():number for number,name in enumerate(calendar.month_abbr) if name}
        month=months.get(cross_month.group(1)[:3].lower())
        if month:
            year=start.year+(month<start.month)
            return date(year,month,int(cross_month.group(2)))
    return start


def refresh(source,today):
    def update(match):
        raw=match.group(0)
        time=BeautifulSoup(raw,'html.parser').select_one('time[datetime]')
        if not time or event_end(time)>=today:
            return raw
        for present,past in PAST_FORMS.items():
            raw=raw.replace(present,past,1)
        return raw
    return re.sub(r'<p(?:\s[^>]*)?>\s*<time\b.*?</p>',update,source,flags=re.S)


def main():
    path=ROOT/'index.html'
    original=path.read_text()
    revised=refresh(original,datetime.now(ZoneInfo('America/Chicago')).date())
    if revised!=original:
        path.write_text(revised)
        print('Updated past event wording.')
    else:
        print('Dated event wording is current.')

if __name__=='__main__':
    main()
