from django.contrib.auth import get_user_model
from django.test import TestCase


class ChangePasswordTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='usuario-teste',
            password='SenhaAtual123!'
        )

    def test_usuario_autenticado_pode_alterar_senha(self):
        self.client.force_login(self.user)

        response = self.client.post('/accounts/alterar-senha/', {
            'old_password': 'SenhaAtual123!',
            'new_password1': 'NovaSenhaSegura123!',
            'new_password2': 'NovaSenhaSegura123!',
        })

        self.assertRedirects(response, '/dashboard/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NovaSenhaSegura123!'))

    def test_senha_atual_invalida_nao_altera_senha(self):
        self.client.force_login(self.user)

        response = self.client.post('/accounts/alterar-senha/', {
            'old_password': 'senha-incorreta',
            'new_password1': 'NovaSenhaSegura123!',
            'new_password2': 'NovaSenhaSegura123!',
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('SenhaAtual123!'))

    def test_formulario_exibe_labels_em_portugues_e_botoes_de_visualizacao(self):
        self.client.force_login(self.user)

        response = self.client.get('/accounts/alterar-senha/')

        self.assertContains(response, 'Senha atual')
        self.assertContains(response, 'Nova senha')
        self.assertContains(response, 'Confirme a nova senha')
        self.assertEqual(
            response.content.decode().count('data-toggle-password='),
            3
        )

    def test_troca_de_senha_exige_login(self):
        response = self.client.get('/accounts/alterar-senha/')

        self.assertRedirects(
            response,
            '/accounts/login/?next=/accounts/alterar-senha/'
        )

# Create your tests here.
