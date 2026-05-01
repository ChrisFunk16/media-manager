#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler - Automatische Downloads nach Zeitplan
Aufruf:
  python scheduler.py          -> Dauerschleife (prüft jede Minute)
  python scheduler.py --once   -> Nur fällige Jobs einmalig ausführen
"""

import json
import sys
import time
import subprocess
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCRIPTS = Path(__file__).parent
JOBS_FILE = BASE_DIR / "jobs.json"


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def load_jobs():
    if not JOBS_FILE.exists():
        return {"jobs": []}
    try:
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"jobs": []}


def save_jobs(data):
    with open(JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_job(job):
    url = job.get('url', '')
    name = job.get('name', 'Unbekannt')
    print(f"\n{Colors.BOLD}▶ Starte Job: {name}{Colors.END}")
    print(f"  URL: {url}")
    result = subprocess.run([sys.executable, str(SCRIPTS / "media-downloader.py"), url])
    return result.returncode == 0


def is_due(job):
    if not job.get('enabled', True):
        return False
    schedule = job.get('schedule', '')
    if not schedule:
        return False

    now = datetime.datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    last_run = job.get('last_run') or ''

    if last_run.startswith(today_str):
        return False

    try:
        scheduled_time = datetime.datetime.strptime(schedule, '%H:%M').time()
        scheduled_dt = datetime.datetime.combine(now.date(), scheduled_time)
        return now >= scheduled_dt
    except ValueError:
        return False


def run_due_jobs():
    data = load_jobs()
    jobs = data.get('jobs', [])

    if not jobs:
        print(f"{Colors.YELLOW}Keine Jobs konfiguriert.{Colors.END}")
        return

    ran_any = False
    for i, job in enumerate(jobs):
        if is_due(job):
            ran_any = True
            success = run_job(job)
            data['jobs'][i]['last_run'] = datetime.datetime.now().isoformat()
            save_jobs(data)
            status = f"{Colors.GREEN}✅{Colors.END}" if success else f"{Colors.RED}❌{Colors.END}"
            print(f"{status} Job '{job['name']}' abgeschlossen")

    if not ran_any:
        print(f"{Colors.BLUE}Keine fälligen Jobs.{Colors.END}")


def run_scheduler_loop():
    print(f"{Colors.BOLD}Scheduler gestartet - Strg+C zum Beenden{Colors.END}\n")
    while True:
        now_str = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"\r[{now_str}] Prüfe Jobs...", end='', flush=True)

        data = load_jobs()
        for i, job in enumerate(data.get('jobs', [])):
            if is_due(job):
                print()
                success = run_job(job)
                data['jobs'][i]['last_run'] = datetime.datetime.now().isoformat()
                save_jobs(data)
                status = "✅" if success else "❌"
                print(f"{status} Job '{job['name']}' abgeschlossen")

        time.sleep(60)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        run_due_jobs()
    else:
        try:
            run_scheduler_loop()
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Scheduler beendet.{Colors.END}")
