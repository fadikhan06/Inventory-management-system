"""
Management command to restore the database from a backup file.
Usage: python manage.py restore_db <backup_file>
"""
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Restore the database from a backup file.'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='Path to the backup file.')

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        if not backup_file.exists():
            raise CommandError(f'Backup file not found: {backup_file}')

        db = settings.DATABASES['default']
        if db['ENGINE'] == 'django.db.backends.sqlite3':
            import shutil
            shutil.copy2(backup_file, db['NAME'])
            self.stdout.write(self.style.SUCCESS(f'SQLite restored from {backup_file}'))

        elif db['ENGINE'] == 'django.db.backends.mysql':
            cmd = [
                'mysql',
                f"--host={db.get('HOST', 'localhost')}",
                f"--port={db.get('PORT', '3306')}",
                f"--user={db.get('USER', 'root')}",
                f"--password={db.get('PASSWORD', '')}",
                db['NAME'],
            ]
            with open(backup_file, 'r') as f:
                subprocess.run(cmd, stdin=f, check=True)
            self.stdout.write(self.style.SUCCESS(f'MySQL restored from {backup_file}'))
        else:
            self.stdout.write(self.style.ERROR('Unsupported database engine for restore.'))
