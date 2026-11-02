#!/usr/bin/env python3
"""Install the user-authorized daily local Scholar check as a macOS LaunchAgent."""
import os
from pathlib import Path
import plistlib
import subprocess

ROOT=Path(__file__).resolve().parent.parent
LABEL='us.ruijiezhu.website-scholar-sync'

def main():
    home=Path.home()
    agent=home/'Library/LaunchAgents'/f'{LABEL}.plist'
    logs=home/'Library/Logs'
    interpreter=ROOT/'.venv-scrape/bin/python'
    if not interpreter.exists():
        raise SystemExit('The local project virtual environment must be installed first.')
    agent.parent.mkdir(parents=True,exist_ok=True)
    logs.mkdir(parents=True,exist_ok=True)
    configuration={
        'Label':LABEL,
        'ProgramArguments':[str(interpreter),str(ROOT/'scripts/local_update.py')],
        'WorkingDirectory':str(ROOT),
        'StartCalendarInterval':{'Hour':10,'Minute':15},
        'RunAtLoad':True,
        'ProcessType':'Background',
        'StandardOutPath':str(logs/'PersonalWebsiteSync.log'),
        'StandardErrorPath':str(logs/'PersonalWebsiteSync.log'),
        'EnvironmentVariables':{'PATH':'/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin','PYTHONUNBUFFERED':'1'}
    }
    if agent.exists() and plistlib.loads(agent.read_bytes())!=configuration:
        raise SystemExit('An existing schedule differs; inspect it before replacing.')
    agent.write_bytes(plistlib.dumps(configuration))
    domain=f'gui/{os.getuid()}'
    loaded=subprocess.run(['launchctl','print',f'{domain}/{LABEL}'],capture_output=True).returncode==0
    if not loaded:
        subprocess.run(['launchctl','bootstrap',domain,str(agent)],check=True)
    print(f'Daily local Scholar update installed for 10:15 local time: {agent}')

if __name__=='__main__':
    main()
