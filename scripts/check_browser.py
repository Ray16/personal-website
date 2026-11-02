#!/usr/bin/env python3
"""Regression checks for the public website. Requires Playwright and a running preview."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import argparse
parser=argparse.ArgumentParser(description='Check responsive layout and interactive behavior with Playwright.')
parser.add_argument('--url',default='http://127.0.0.1:8765')
parser.add_argument('--browser-executable',default=None)
parser.add_argument('--screenshots',type=Path,default=None)
args=parser.parse_args()
BASE=args.url.rstrip('/')
OUT=args.screenshots
if OUT: OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path=args.browser_executable)
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    failures=[]
    page.on('pageerror',lambda error:failures.append(str(error)))
    for width in [1440,1024,768,600,390,320]:
        page.set_viewport_size({'width':width,'height':1000})
        for name in ['index.html','publications.html','project.html','poster.html','presentation.html','hobby.html','link.html','resume.html']:
            page.goto(BASE+'/'+name,wait_until='networkidle')
            page.emulate_media(reduced_motion='reduce')
            page.wait_for_timeout(100)
            assert page.locator('h1').count()==1,(name,'h1')
            overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
            if overflow: failures.append(f'{name} overflows at {width}px')
            page.locator('img').evaluate_all('(imgs)=>imgs.forEach(i=>i.loading="eager")')
            page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
            broken=page.locator('img').evaluate_all('(imgs)=>imgs.filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src)')
            if broken: failures.append(f'{name}: {broken}')
            if OUT and width in [1440,390] and name in ['index.html','publications.html','project.html','poster.html','hobby.html']:
                page.screenshot(path=str(OUT/f'{name[:-5]}-{width}.png'),full_page=True)
        print('Layout checked:',width,flush=True)
    page.set_viewport_size({'width':390,'height':844})
    page.goto(BASE+'/index.html',wait_until='networkidle')
    assert page.locator('.news-year-group p:visible').count()==6
    for year in ['2026','2025','2024','2023','2022','all','recent']:
        page.locator(f'button[data-year="{year}"]').click()
        if year not in ['all','recent']:
            assert page.locator('.news-year-group:not(.hidden)').count()==1
            assert page.locator('.news-year-group:not(.hidden)').get_attribute('data-year')==year
        print('News filter checked:',year,flush=True)
    page.evaluate('window.scrollTo(0,0)')
    page.locator('#nav-toggle').click()
    assert page.locator('#nav-toggle').get_attribute('aria-expanded')=='true'
    page.keyboard.press('Escape')
    assert page.locator('#nav-toggle').get_attribute('aria-expanded')=='false'
    assert page.locator('#nav-toggle').evaluate('(el)=>document.activeElement===el')
    page.locator('#nav-toggle').click()
    page.get_by_role('link',name='Projects',exact=True).click()
    assert page.url.endswith('project.html')
    assert page.locator('#nav-toggle').get_attribute('aria-expanded')=='false'
    print('Mobile navigation checked',flush=True)
    page.locator('#theme-toggle').click()
    expected=page.locator('html').get_attribute('data-theme')
    page.reload(wait_until='networkidle')
    assert page.locator('html').get_attribute('data-theme')==expected
    page.set_viewport_size({'width':1440,'height':1000})
    page.goto(BASE+'/index.html',wait_until='networkidle')
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    if OUT: page.screenshot(path=str(OUT/'index-dark.png'),full_page=True)
    print('Theme persistence checked',flush=True)
    assert page.locator('.intro-text').evaluate('(el)=>getComputedStyle(el).animationName')=='none'
    print('Reduced motion checked',flush=True)
    context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
    fallback=context.new_page();fallback.goto(BASE+'/index.html',wait_until='networkidle')
    assert fallback.get_by_role('link',name='Publications',exact=True).is_visible()
    assert fallback.locator('.news-year-group p:visible').count()>6
    print('No-JavaScript access checked',flush=True)
    context.close()
    normal=browser.new_context(reduced_motion='no-preference',color_scheme='light')
    normal_page=normal.new_page()
    normal_page.goto(BASE+'/index.html',wait_until='networkidle')
    assert normal_page.locator('.intro-text').evaluate('(el)=>getComputedStyle(el).animationName')=='enter'
    assert normal_page.locator('html').get_attribute('data-theme')=='light'
    normal.close()
    blocked=browser.new_context(color_scheme='dark')
    blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})")
    blocked_page=blocked.new_page()
    blocked_page.goto(BASE+'/index.html',wait_until='networkidle')
    assert blocked_page.locator('html').get_attribute('data-theme')=='dark'
    blocked_page.locator('#theme-toggle').click()
    assert blocked_page.locator('html').get_attribute('data-theme')=='light'
    assert blocked_page.locator('.news-year-group p:visible').count()==6
    print('System theme, normal motion, and blocked-storage fallback checked',flush=True)
    blocked.close()
    browser.close()
    assert not failures,failures
    print('PASS: all layout and interaction checks')
