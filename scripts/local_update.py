#!/usr/bin/env python3
"""Daily local Scholar updater. Use an isolated checkout and push only validated generated content."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime
from publications import PROFILE_URL, fetch, parse_profile

REPOSITORY='https://github.com/Ray16/personal-website.git'


def run(args,cwd=None):
    env={**os.environ,'GIT_TERMINAL_PROMPT':'0','PYTHONUNBUFFERED':'1'}
    subprocess.run(args,cwd=cwd,env=env,check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Read Scholar without writing files or pushing changes')
    args=parser.parse_args()
    print(datetime.now().isoformat(timespec='seconds')+' Starting local Scholar check.',flush=True)
    if args.check:
        records=parse_profile(fetch(PROFILE_URL))
        print(f'PASS: public Scholar profile accessible locally; {len(records)} records.',flush=True)
        return
    with tempfile.TemporaryDirectory(prefix='rayzhu-website-sync-') as directory:
        checkout=Path(directory)/'site'
        run(['git','clone','--quiet','--depth','1','--branch','main',REPOSITORY,str(checkout)])
        run([sys.executable,str(checkout/'scripts/publications.py')],checkout)
        changed=subprocess.check_output(['git','diff','--name-only'],cwd=checkout,text=True)
        if 'data/publications.json' in changed:
            run([sys.executable,str(checkout/'scripts/refresh_thumbnails.py'),'--limit','3'],checkout)
            run([sys.executable,str(checkout/'scripts/publications.py'),'--render-only'],checkout)
        run([sys.executable,str(checkout/'scripts/refresh_news.py')],checkout)
        run([sys.executable,str(checkout/'scripts/check_site.py')],checkout)
        run([sys.executable,'-m','unittest','discover','-s','scripts','-p','test_content.py'],checkout)
        run(['git','add','data/publications.json','publications.html','index.html','assets/pubs'],checkout)
        if subprocess.run(['git','diff','--cached','--quiet'],cwd=checkout).returncode==0:
            print('Website content is current; no commit needed.',flush=True)
            return
        run(['git','-c','user.name=Ray Zhu','-c','user.email=rzhu16@uchicago.edu','commit','-m','Update publications from the public Scholar profile'],checkout)
        run(['git','pull','--rebase','origin','main'],checkout)
        run(['git','push','origin','main'],checkout)
        print('Verified content pushed to GitHub; the normal deployment checks will run.',flush=True)

if __name__=='__main__':
    main()
