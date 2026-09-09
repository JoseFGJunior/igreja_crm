from django.contrib.auth.models import Permission
from datetime import date
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Usuario, UsuarioIgreja
from apps.igrejas.models import Igreja
from apps.membros.models import Membro
from apps.membros.views import normalizar_whatsapp


class PermissaoMembroTestCase(TestCase):
    def setUp(self):
        self.igreja = Igreja.objects.create(nome='Igreja Teste', slug='igreja-teste')
        self.usuario = Usuario.objects.create_user(username='cadastro', password='senha-segura')
        UsuarioIgreja.objects.create(usuario=self.usuario, igreja=self.igreja, igreja_default=True)
        self.client.force_login(self.usuario)
        session = self.client.session
        session['igreja_id'] = self.igreja.id
        session.save()

    def test_usuario_sem_permissao_nao_acessa_lista_de_membros(self):
        response = self.client.get(reverse('membro_list'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_com_permissao_de_cadastro_acessa_apenas_novo_membro(self):
        self.usuario.user_permissions.add(Permission.objects.get(codename='add_membro'))
        self.assertEqual(self.client.get(reverse('membro_create')).status_code, 200)
        self.assertEqual(self.client.get(reverse('membro_list')).status_code, 403)

    def test_lista_filtra_por_status_e_preserva_pesquisa_por_nome(self):
        self.usuario.user_permissions.add(Permission.objects.get(codename='view_membro'))
        Membro.objects.create(igreja=self.igreja, nome='Maria Membro', status='MEMBRO')
        Membro.objects.create(igreja=self.igreja, nome='Maria Visitante', status='VISITANTE')

        response = self.client.get(
            reverse('membro_list'),
            {'q': 'Maria', 'status': 'MEMBRO'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maria Membro')
        self.assertNotContains(response, 'Maria Visitante')
        self.assertEqual(response.context['status'], 'MEMBRO')
        self.assertEqual(response.context['total_membros'], 1)

class VisitanteTestCase(TestCase):
    def setUp(self):
        self.igreja_a = Igreja.objects.create(nome='Igreja A', slug='igreja-a')
        self.igreja_b = Igreja.objects.create(nome='Igreja B', slug='igreja-b')
        self.usuario = Usuario.objects.create_user(username='visitantes', password='senha-segura')
        UsuarioIgreja.objects.create(usuario=self.usuario, igreja=self.igreja_a, igreja_default=True)
        for codename in ('view_membro', 'add_membro', 'change_membro'):
            self.usuario.user_permissions.add(Permission.objects.get(codename=codename))
        self.client.force_login(self.usuario)
        session = self.client.session
        session['igreja_id'] = self.igreja_a.id
        session.save()

    def test_cadastro_cria_primeira_visita_e_jornada(self):
        response = self.client.post(reverse('visitante_create'), {
            'nome': 'Maria',
            'whatsapp': '(81) 99999-9999',
            'telefone': '',
            'data_primeira_visita': '2026-08-23',
            'origem_visitante': 'Convite',
            'observacao_visitante': '',
            'responsavel_visitante': '',
        })

        self.assertEqual(response.status_code, 302)
        visitante = Membro.objects.get(nome='Maria')
        self.assertEqual(visitante.igreja, self.igreja_a)
        self.assertEqual(visitante.whatsapp, '5581999999999')
        self.assertEqual(visitante.visitas_visitante.count(), 1)
        self.assertEqual(visitante.acompanhamentos_visitante.count(), 3)
        self.assertEqual(
            set(visitante.acompanhamentos_visitante.values_list('data_prevista', flat=True)),
            {date(2026, 8, 24), date(2026, 8, 30), date(2026, 9, 7)},
        )

    def test_visitante_de_outra_igreja_nao_e_exibido(self):
        Membro.objects.create(
            igreja=self.igreja_b,
            nome='Visitante B',
            status='VISITANTE',
            whatsapp='81988888888',
            data_primeira_visita=date(2026, 8, 23),
        )

        response = self.client.get(reverse('visitante_list'))

        self.assertNotContains(response, 'Visitante B')

    def test_usuario_sem_permissao_nao_acessa_modulo(self):
        self.usuario.user_permissions.clear()

        self.assertEqual(self.client.get(reverse('visitante_dashboard')).status_code, 403)

    def test_whatsapp_adiciona_codigo_do_brasil_e_remove_mascara(self):
        self.assertEqual(
            normalizar_whatsapp('(81) 98841-4026'),
            '5581988414026'
        )
        self.assertEqual(
            normalizar_whatsapp('5581988414026'),
            '5581988414026'
        )
