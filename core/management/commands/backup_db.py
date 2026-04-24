"""
Management command to backup the database (SQLite or MySQL via mysqldump).
Usage: python manage.py backup_db
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup the database to the backups/ directory.'

    def handle(self, *args, **options):
        backup_dir = getattr(settings, 'BACKUP_DIR', Path(settings.BASE_DIR) / 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db = settings.DATABASES['default']

        if db['ENGINE'] == 'django.db.backends.sqlite3':
            src = db['NAME']
            dest = Path(backup_dir) / f'backup_{timestamp}.sqlite3'
            import shutil
            shutil.copy2(src, dest)
            self.stdout.write(self.style.SUCCESS(f'SQLite backup saved to {dest}'))

        elif db['ENGINE'] == 'django.db.backends.mysql':
            dest = Path(backup_dir) / f'backup_{timestamp}.sql'
            cmd = [
                'mysqldump',
                f"--host={db.get('HOST', 'localhost')}",
                f"--port={db.get('PORT', '3306')}",
                f"--user={db.get('USER', 'root')}",
                f"--password={db.get('PASSWORD', '')}",
                db['NAME'],
            ]
            with open(dest, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            self.stdout.write(self.style.SUCCESS(f'MySQL backup saved to {dest}'))
        else:
            self.stdout.write(self.style.ERROR('Unsupported database engine for backup.'))
