from django.core.management.base import BaseCommand, CommandError

from apps.mobile.push import send_push_notification


class Command(BaseCommand):
    help = 'Envia uma notificação Web Push para as inscrições ativas.'

    def add_arguments(self, parser):
        parser.add_argument('--title', required=True)
        parser.add_argument('--body', required=True)
        parser.add_argument('--tenant', default='')
        parser.add_argument('--url', default='/')

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.PUSH_VAPID_PRIVATE_KEY or not settings.PUSH_VAPID_PUBLIC_KEY:
            raise CommandError('Configure PUSH_VAPID_PUBLIC_KEY e PUSH_VAPID_PRIVATE_KEY no ambiente.')
        sent, removed = send_push_notification(title=options['title'], body=options['body'], tenant=options['tenant'] or None, url=options['url'])
        self.stdout.write(self.style.SUCCESS(f'{sent} notificação(ões) enviada(s); {removed} inscrição(ões) removida(s).'))
