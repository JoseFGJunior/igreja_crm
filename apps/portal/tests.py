from django.test import TestCase

from apps.igrejas.models import Igreja
from apps.portal.models import ConfiguracaoSiteIgreja


class PortalSlugTests(TestCase):
    def setUp(self):
        self.igreja = Igreja.objects.create(
            nome='PIB Cruz',
            slug='pibcruz',
        )

    def test_uses_church_slug_when_public_slug_is_null(self):
        ConfiguracaoSiteIgreja.objects.create(
            igreja=self.igreja,
            slug_publico=None,
        )

        response = self.client.get('/pibcruz/')

        self.assertEqual(response.status_code, 200)

    def test_uses_church_slug_when_public_slug_is_empty(self):
        ConfiguracaoSiteIgreja.objects.create(
            igreja=self.igreja,
            slug_publico='',
        )

        response = self.client.get('/pibcruz/')

        self.assertEqual(response.status_code, 200)