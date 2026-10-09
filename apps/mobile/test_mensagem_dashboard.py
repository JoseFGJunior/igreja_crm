from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Usuario, UsuarioIgreja
from apps.igrejas.models import Igreja
from apps.mobile.models import MensagemApp


class MensagemDashboardTests(TestCase):
    def setUp(self):
        self.igreja = Igreja.objects.create(nome='Igreja Teste', slug='igreja-teste')
        self.outra = Igreja.objects.create(nome='Outra Igreja', slug='outra-igreja')
        self.usuario = Usuario.objects.create_user(
            username='mensagens',
            password='senha-segura',
        )
        UsuarioIgreja.objects.create(
            usuario=self.usuario,
            igreja=self.igreja,
            igreja_default=True,
        )
        self.usuario.user_permissions.add(
            Permission.objects.get(codename='view_mensagemapp')
        )
        self.client.force_login(self.usuario)
        session = self.client.session
        session['igreja_id'] = self.igreja.id
        session.save()

    def test_dashboard_exige_permissao(self):
        self.usuario.user_permissions.clear()
        response = self.client.get(reverse('mensagem_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_isola_mensagens_da_igreja_selecionada(self):
        MensagemApp.objects.create(
            igreja=self.igreja,
            titulo='Mensagem da minha igreja',
            youtube_url='https://youtu.be/minha',
        )
        MensagemApp.objects.create(
            igreja=self.outra,
            titulo='Mensagem de outra igreja',
            youtube_url='https://youtu.be/outra',
        )

        response = self.client.get(reverse('mensagem_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mensagem da minha igreja')
        self.assertNotContains(response, 'Mensagem de outra igreja')
        self.assertEqual(response.context['total_mensagens'], 1)
