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
    def test_redirects_public_slug_to_app_and_adds_tenant(self):
        ConfiguracaoSiteIgreja.objects.create(
            igreja=self.igreja,
            destino_publico=ConfiguracaoSiteIgreja.DESTINO_APP,
            url_app_web='https://eloperfeito.net.br/app/',
        )

        response = self.client.get('/pibcruz/?tenant=PIBCRUZ')

        self.assertRedirects(
            response,
            'https://eloperfeito.net.br/app/?tenant=pibcruz',
            fetch_redirect_response=False,
        )

    def test_avoids_redirect_loop_when_app_url_is_public_slug(self):
        ConfiguracaoSiteIgreja.objects.create(
            igreja=self.igreja,
            destino_publico=ConfiguracaoSiteIgreja.DESTINO_APP,
            url_app_web='http://testserver/pibcruz',
        )

        response = self.client.get('/pibcruz/?tenant=PIBCRUZ')

        self.assertRedirects(
            response,
            'http://testserver/app/?tenant=pibcruz',
            fetch_redirect_response=False,
        )

    def test_contribution_uses_generated_pix_qr_code(self):
        ConfiguracaoSiteIgreja.objects.create(
            igreja=self.igreja,
            pix_chave='12345678901',
            cidade='Igarassu',
        )

        response = self.client.get('/pibcruz/')

        self.assertContains(response, 'href="#pix-modal"')
        self.assertContains(response, '/api/mobile/v1/pix/qr-code/?tenant=pibcruz')
        self.assertContains(response, 'Pix copia e cola')
        self.assertContains(response, '12345678901')