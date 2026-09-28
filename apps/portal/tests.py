from datetime import date

from django.test import TestCase

from apps.igrejas.models import Igreja
from apps.portal.models import ConfiguracaoSiteIgreja
from apps.membros.models import Membro


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

    def test_shows_authorized_birthday_member_on_public_page(self):
        ConfiguracaoSiteIgreja.objects.create(igreja=self.igreja)
        today = date.today()
        Membro.objects.create(
            igreja=self.igreja,
            nome='Ana Aniversariante',
            data_nascimento=date(1990, today.month, today.day),
            autoriza_exibir_aniversario_site=True,
        )
        Membro.objects.create(
            igreja=self.igreja,
            nome='Pessoa Sem Autorização',
            data_nascimento=date(1990, today.month, today.day),
        )

        response = self.client.get('/pibcruz/')

        self.assertContains(response, 'Ana Aniversariante')
        self.assertNotContains(response, 'Pessoa Sem Autorização')
