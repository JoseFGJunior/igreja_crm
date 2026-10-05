import json

from django.conf import settings
from django.utils import timezone

from .models import PushSubscription


def send_push_notification(*, title, body, tenant=None, url='/'):
    from pywebpush import WebPushException, webpush

    queryset = PushSubscription.objects.filter(ativo=True)
    if tenant:
        queryset = queryset.filter(igreja__slug__iexact=tenant)
    payload = json.dumps({'title': title, 'body': body, 'url': url})
    sent = 0
    removed = 0
    for subscription in queryset.iterator():
        try:
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {'p256dh': subscription.p256dh, 'auth': subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={'sub': settings.PUSH_VAPID_CLAIMS_EMAIL},
            )
            subscription.ultimo_uso_em = timezone.now()
            subscription.save(update_fields=('ultimo_uso_em', 'updated_at'))
            sent += 1
        except WebPushException as error:
            response = getattr(error, 'response', None)
            if response is not None and response.status_code in (404, 410):
                subscription.ativo = False
                subscription.save(update_fields=('ativo', 'updated_at'))
                removed += 1
    return sent, removed
