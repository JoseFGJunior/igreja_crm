from datetime import date, timedelta

from django.test import TestCase

from apps.eventos.models import Evento
from apps.igrejas.models import Igreja
from apps.mobile.models import ConfiguracaoApp, PalavraDoDia, PedidoOracao


class MobileApiTests(TestCase):
    def setUp(self):
        self.igreja = Igreja.objects.create(nome='PIB Cruz', slug='pibcruz')
        self.outra = Igreja.objects.create(nome='Outra Igreja', slug='outra')
        ConfiguracaoApp.objects.create(igreja=self.igreja, ativo=True, nome_exibicao='PIB Cruz App')

    def test_palavra_do_dia_exige_publicacao(self):
        palavra = PalavraDoDia.objects.create(igreja=self.igreja, data=date.today(), titulo='Rascunho')
        self.assertEqual(self.client.get('/api/mobile/v1/palavra-do-dia/').status_code, 404)
        palavra.status = PalavraDoDia.STATUS_PUBLICADO
        palavra.publicado = True
        palavra.save()
        response = self.client.get('/api/mobile/v1/palavra-do-dia/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['titulo'], 'Rascunho')

    def test_api_isola_conteudo_por_igreja(self):
        PalavraDoDia.objects.create(igreja=self.outra, data=date.today(), titulo='Outra')
        PalavraDoDia.objects.create(igreja=self.igreja, data=date.today(), titulo='Minha', status=PalavraDoDia.STATUS_APROVADO, publicado=True)
        response = self.client.get('/api/mobile/v1/palavra-do-dia/')
        self.assertEqual(response.json()['titulo'], 'Minha')

    def test_home_agrega_igreja_palavra_e_eventos(self):
        PalavraDoDia.objects.create(igreja=self.igreja, data=date.today(), titulo='Hoje', status=PalavraDoDia.STATUS_APROVADO, publicado=True)
        Evento.objects.create(igreja=self.igreja, titulo='Culto', data=date.today() + timedelta(days=1))
        response = self.client.get('/api/mobile/v1/home/')
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['igreja']['nome_exibicao'], 'PIB Cruz App')
        self.assertEqual(payload['palavra_dia']['titulo'], 'Hoje')
        self.assertEqual(payload['proximos_eventos'][0]['titulo'], 'Culto')
    def test_pedido_de_oracao_recebe_nome_telefone_e_pedido(self):
        response = self.client.post('/api/mobile/v1/pedidos-oracao/', data={
            'nome': 'Maria',
            'telefone': '(81) 99999-8888',
            'pedido': 'Peço oração pela minha família.',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        pedido = PedidoOracao.objects.get()
        self.assertEqual(pedido.igreja, self.igreja)
        self.assertEqual(pedido.telefone, '(81) 99999-8888')
        self.assertEqual(pedido.pedido, 'Peço oração pela minha família.')

    def test_pedido_de_oracao_exige_telefone_e_pedido(self):
        response = self.client.post('/api/mobile/v1/pedidos-oracao/', data={'nome': 'Maria'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PedidoOracao.objects.count(), 0)
    def test_home_uses_requested_tenant(self):
        ConfiguracaoApp.objects.create(igreja=self.outra, ativo=True, nome_exibicao='Outra Igreja App')
        PalavraDoDia.objects.create(
            igreja=self.outra,
            data=date.today(),
            titulo='Palavra da Outra',
            status=PalavraDoDia.STATUS_APROVADO,
            publicado=True,
        )

        response = self.client.get('/api/mobile/v1/home/?tenant=outra')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['igreja']['nome_exibicao'], 'Outra Igreja App')
        self.assertEqual(response.json()['palavra_dia']['titulo'], 'Palavra da Outra')

    def test_pedido_de_oracao_uses_requested_tenant(self):
        ConfiguracaoApp.objects.create(igreja=self.outra, ativo=True, nome_exibicao='Outra Igreja App')

        response = self.client.post('/api/mobile/v1/pedidos-oracao/', data={
            'tenant': 'outra',
            'nome': 'João',
            'telefone': '(81) 98888-7777',
            'pedido': 'Pedido da outra igreja.',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PedidoOracao.objects.get().igreja, self.outra)