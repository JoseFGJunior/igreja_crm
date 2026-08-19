#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def get_environment():
    environment = os.environ.get('ENVIRONMENT')

    if environment:
        return environment.lower()

    environment_file = Path(__file__).resolve().parent / '.env'

    if not environment_file.exists():
        return 'development'

    for line in environment_file.read_text(encoding='utf-8').splitlines():
        if line.startswith('ENVIRONMENT='):
            return line.split('=', 1)[1].strip().lower()

    return 'development'


def protect_production_commands():
    if get_environment() != 'production' or len(sys.argv) < 2:
        return

    command = sys.argv[1]

    if command in {'test', 'makemigrations', 'runserver', 'flush'}:
        raise SystemExit(
            f'O comando "{command}" é bloqueado em PRODUÇÃO. '
            'Use o ambiente development.'
        )

    if (
        command == 'migrate'
        and os.environ.get('ALLOW_PRODUCTION_MIGRATIONS') != 'true'
    ):
        raise SystemExit(
            'Migrations em PRODUÇÃO exigem aprovação explícita. '
            'Defina ALLOW_PRODUCTION_MIGRATIONS=true somente para '
            'executar a migration revisada.'
        )


def main():
    """Run administrative tasks."""
    protect_production_commands()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
