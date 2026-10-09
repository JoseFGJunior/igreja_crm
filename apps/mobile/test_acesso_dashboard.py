from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Usuario, UsuarioIgreja
from apps.igrejas.models import Igreja
from apps.mobile.models import AcessoApp


class AcessoDashboardTests(TestCase):
    def setUp(self):
        self.igreja = Igreja.objects.create(nome='Igreja Teste', slug='igreja-teste')
        self.outra = Igreja.objects.create(nome='Outra Igreja', slug='outra-igreja')
        self.usuario = Usuario.objects.create_user(
            username='acessos',
            password='senha-segura',
        )
        UsuarioIgreja.objects.create(
            usuario=self.usuario,
            igreja=self.igreja,
            igreja_default=True,
        )
        self.usuario.user_permissions.add(
            Permission.objects.get(codename='view_acessoapp')
        )
        self.client.force_login(self.usuario)
        session = self.client.session
        session['igreja_id'] = self.igreja.id
        session.save()

    def test_dashboard_exige_permissao(self):
        self.usuario.user_permissions.clear()
        response = self.client.get(reverse('acesso_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_isola_acessos_da_igreja_selecionada(self):
        AcessoApp.objects.create(
            igreja=self.igreja,
            visitante_id='visitante-1',
            evento='home',
            recurso='mensagens',
        )
        AcessoApp.objects.create(
            igreja=self.outra,
            visitante_id='visitante-2',
            evento='home',
            recurso='outra-igreja',
        )

        response = self.client.get(reverse('acesso_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mensagens')
        self.assertNotContains(response, 'outra-igreja')
        self.assertEqual(response.context['total_acessos'], 1)
        self.assertEqual(response.context['visitantes_unicos'], 1)
