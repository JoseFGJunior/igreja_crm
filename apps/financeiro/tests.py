from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.models import UsuarioIgreja
from apps.financeiro.models import CategoriaFinanceira
from apps.financeiro.models import LancamentoFinanceiro
from apps.financeiro.models import FechamentoFinanceiroMensal
from apps.igrejas.models import Igreja

class FinanceiroTestCase(TestCase):

    def setUp(self):
        self.igreja = Igreja.objects.create(
            nome='Igreja Teste',
            slug='igreja-teste',
            plano=Igreja.PLANO_COMPLETO
        )
        self.usuario = Usuario.objects.create_user(
            username='tesoureiro',
            password='senha-segura'
        )
        UsuarioIgreja.objects.create(
            usuario=self.usuario,
            igreja=self.igreja,
            igreja_default=True
        )
        self.categoria = CategoriaFinanceira.objects.create(
            igreja=self.igreja,
            nome='Despesas gerais',
            tipo=CategoriaFinanceira.TIPO_SAIDA
        )
        self.client.force_login(self.usuario)
        session = self.client.session
        session['igreja_id'] = self.igreja.id
        session.save()

    def test_cria_compra_em_dez_parcelas_mensais(self):
        response = self.client.post(
            reverse('financeiro_despesa_recorrente_create'),
            {
                'tipo_geracao': 'PARCELADA',
                'data_primeiro_vencimento': '2026-06-15',
                'categoria': self.categoria.id,
                'descricao': 'TV',
                'valor_parcela': '100.00',
                'quantidade': '10',
                'forma_pagamento': LancamentoFinanceiro.FORMA_CARTAO,
                'observacao': '',
            }
        )

        self.assertRedirects(
            response,
            reverse('financeiro_conta_pagar_list')
        )
        parcelas = LancamentoFinanceiro.objects.order_by('data')
        self.assertEqual(parcelas.count(), 10)
        self.assertEqual(parcelas.first().descricao, 'TV - Parcela 1/10')
        self.assertEqual(parcelas.first().valor, Decimal('100.00'))
        self.assertEqual(parcelas.last().data, date(2027, 3, 15))
        self.assertEqual(parcelas.last().numero_parcela, 10)
        self.assertEqual(parcelas.last().total_parcelas, 10)
        self.assertEqual(
            parcelas.values('grupo_recorrencia').distinct().count(),
            1
        )

    def test_exibe_formulario_de_despesa_recorrente(self):
        response = self.client.get(
            reverse('financeiro_despesa_recorrente_create')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Nova despesa recorrente ou parcelada'
        )
        self.assertContains(response, 'Gerar despesas')

    def test_ajusta_recorrencia_para_o_ultimo_dia_do_mes(self):
        self.client.post(
            reverse('financeiro_despesa_recorrente_create'),
            {
                'tipo_geracao': 'RECORRENTE',
                'data_primeiro_vencimento': '2026-01-31',
                'categoria': self.categoria.id,
                'descricao': 'Internet',
                'valor_parcela': '150.00',
                'quantidade': '3',
                'forma_pagamento': LancamentoFinanceiro.FORMA_BOLETO,
                'observacao': '',
            }
        )

        datas = list(
            LancamentoFinanceiro.objects.order_by('data').values_list(
                'data',
                flat=True
            )
        )
        self.assertEqual(
            datas,
            [
                date(2026, 1, 31),
                date(2026, 2, 28),
                date(2026, 3, 31),
            ]
        )

    def test_dashboard_filtra_totalizadores_e_resumo_pelo_ano(self):
        categoria_entrada = CategoriaFinanceira.objects.create(
            igreja=self.igreja,
            nome='Dizimos',
            tipo=CategoriaFinanceira.TIPO_ENTRADA
        )
        LancamentoFinanceiro.objects.create(
            igreja=self.igreja,
            categoria=categoria_entrada,
            tipo=LancamentoFinanceiro.TIPO_ENTRADA,
            descricao='Entrada 2025',
            valor=Decimal('100.00'),
            data=date(2025, 1, 10)
        )
        LancamentoFinanceiro.objects.create(
            igreja=self.igreja,
            categoria=self.categoria,
            tipo=LancamentoFinanceiro.TIPO_SAIDA,
            descricao='Despesa 2025',
            valor=Decimal('40.00'),
            data=date(2025, 2, 10)
        )
        LancamentoFinanceiro.objects.create(
            igreja=self.igreja,
            categoria=categoria_entrada,
            tipo=LancamentoFinanceiro.TIPO_ENTRADA,
            descricao='Entrada 2026',
            valor=Decimal('300.00'),
            data=date(2026, 1, 10)
        )

        response_2025 = self.client.get(
            reverse('financeiro_dashboard'),
            {'ano': 2025}
        )
        response_2026 = self.client.get(
            reverse('financeiro_dashboard'),
            {'ano': 2026}
        )

        self.assertEqual(response_2025.context['ano_selecionado'], 2025)
        self.assertEqual(response_2025.context['total_entradas'], Decimal('100.00'))
        self.assertEqual(response_2025.context['total_despesas'], Decimal('40.00'))
        self.assertEqual(response_2025.context['saldo'], Decimal('60.00'))
        self.assertEqual(response_2025.context['resumo_anual'][0]['receita'], Decimal('100.00'))
        self.assertEqual(response_2025.context['resumo_anual'][1]['despesa'], Decimal('40.00'))
        self.assertEqual(response_2026.context['total_entradas'], Decimal('300.00'))
        self.assertEqual(response_2026.context['total_despesas'], Decimal('0'))
        self.assertEqual(response_2026.context['saldo'], Decimal('300.00'))
        self.assertNotContains(response_2025, 'Ultimas entradas')
        self.assertNotContains(response_2025, 'Ultimas despesas')

    def test_exportacao_do_resumo_respeita_ano_selecionado(self):
        response = self.client.get(
            reverse('financeiro_resumo_anual_excel'),
            {'ano': 2025}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'resumo-financeiro-2025.xlsx',
            response['Content-Disposition']
        )

    def test_fechamento_calcula_saldo_e_carrega_para_mes_seguinte(self):
        self.usuario.is_staff = True
        self.usuario.save()
        entrada = CategoriaFinanceira.objects.create(igreja=self.igreja, nome='Ofertas', tipo=CategoriaFinanceira.TIPO_ENTRADA)
        LancamentoFinanceiro.objects.create(igreja=self.igreja, categoria=entrada, tipo=LancamentoFinanceiro.TIPO_ENTRADA, descricao='Oferta', valor=Decimal('2000.00'), data=date(2026, 7, 10))
        LancamentoFinanceiro.objects.create(igreja=self.igreja, categoria=self.categoria, tipo=LancamentoFinanceiro.TIPO_SAIDA, descricao='Aluguel', valor=Decimal('1500.00'), data=date(2026, 7, 11))
        response = self.client.post(reverse('financeiro_fechamento_confirmar'), {'ano': 2026, 'mes': 7, 'saldo_inicial': '1000.00'})
        self.assertEqual(response.status_code, 302)
        julho = FechamentoFinanceiroMensal.objects.get(igreja=self.igreja, competencia=date(2026, 7, 1))
        self.assertEqual(julho.saldo_final, Decimal('1500.00'))
        agosto = self.client.get(reverse('financeiro_fechamento_mensal'), {'ano': 2026, 'mes': 8})
        self.assertEqual(agosto.context['saldo_inicial'], Decimal('1500.00'))

    def test_fechamento_aceita_saldo_negativo_sem_alterar_sinal(self):
        self.usuario.is_staff = True
        self.usuario.save()
        LancamentoFinanceiro.objects.create(igreja=self.igreja, categoria=self.categoria, tipo=LancamentoFinanceiro.TIPO_SAIDA, descricao='Despesa', valor=Decimal('200.00'), data=date(2026, 7, 10))
        self.client.post(reverse('financeiro_fechamento_confirmar'), {'ano': 2026, 'mes': 7, 'saldo_inicial': '100.00'})
        fechamento = FechamentoFinanceiroMensal.objects.get(igreja=self.igreja, competencia=date(2026, 7, 1))
        self.assertEqual(fechamento.saldo_final, Decimal('-100.00'))

    def test_lancamento_nao_pode_ser_alterado_em_mes_fechado(self):
        self.usuario.is_staff = True
        self.usuario.save()
        conta = LancamentoFinanceiro.objects.create(igreja=self.igreja, categoria=self.categoria, tipo=LancamentoFinanceiro.TIPO_SAIDA, descricao='Internet', valor=Decimal('100.00'), data=date(2026, 7, 10))
        self.client.post(reverse('financeiro_fechamento_confirmar'), {'ano': 2026, 'mes': 7, 'saldo_inicial': '1000.00'})
        response = self.client.post(reverse('financeiro_conta_pagar_delete', args=[conta.id]))
        self.assertRedirects(response, reverse('financeiro_conta_pagar_list'))
        self.assertTrue(LancamentoFinanceiro.objects.filter(id=conta.id).exists())

    def test_saldo_de_implantacao_so_pode_ser_reconfigurado_na_igreja_atual(self):
        self.usuario.is_staff = True
        self.usuario.save()
        fechamento = FechamentoFinanceiroMensal.objects.create(
            igreja=self.igreja, competencia=date(2026, 7, 1),
            saldo_inicial=Decimal('3500.00'), saldo_final=Decimal('3500.00'),
            origem_saldo_inicial=FechamentoFinanceiroMensal.ORIGEM_IMPLANTACAO,
        )
        response = self.client.post(
            reverse('financeiro_fechamento_configurar_saldo_inicial', args=[fechamento.id]),
            {'saldo_inicial': '0.00'},
        )
        self.assertEqual(response.status_code, 302)
        fechamento.refresh_from_db()
        self.assertEqual(fechamento.saldo_inicial, Decimal('0.00'))
