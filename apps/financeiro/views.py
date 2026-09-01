import calendar
import uuid
from datetime import date
from decimal import Decimal
from io import BytesIO
from string import ascii_uppercase
from xml.sax.saxutils import escape
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import UsuarioIgreja
from apps.financeiro.forms import CategoriaEntradaForm
from apps.financeiro.forms import CategoriaSaidaForm
from apps.financeiro.forms import ContaPagarForm
from apps.financeiro.forms import DespesaRecorrenteForm
from apps.financeiro.forms import EntradaFinanceiraForm
from apps.financeiro.models import CategoriaFinanceira
from apps.financeiro.models import LancamentoFinanceiro
from apps.financeiro.models import FechamentoFinanceiroMensal


MESES_ANO = [
    (1, 'JAN'),
    (2, 'FEV'),
    (3, 'MAR'),
    (4, 'ABR'),
    (5, 'MAI'),
    (6, 'JUN'),
    (7, 'JUL'),
    (8, 'AGO'),
    (9, 'SET'),
    (10, 'OUT'),
    (11, 'NOV'),
    (12, 'DEZ'),
]

MESES_ANO_EXTENSO = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]


def adicionar_meses(data, quantidade):
    mes_base = data.month - 1 + quantidade
    ano = data.year + mes_base // 12
    mes = mes_base % 12 + 1
    dia = min(data.day, calendar.monthrange(ano, mes)[1])

    return data.replace(
        year=ano,
        month=mes,
        day=dia
    )


def get_igreja_selecionada(request):
    igreja_id = request.session.get('igreja_id')

    if not igreja_id:
        return None

    relacao = UsuarioIgreja.objects.select_related('igreja').filter(
        usuario=request.user,
        igreja_id=igreja_id,
        ativo=True,
        igreja__ativa=True
    ).first()

    if relacao:
        return relacao.igreja

    return None


def plano_financeiro_required(view_func):
    def wrapped(request, *args, **kwargs):
        igreja = get_igreja_selecionada(request)

        if igreja is None:
            return redirect('dashboard')

        if not igreja.plano_completo_ativo:
            return render(
                request,
                'financeiro/plano_bloqueado.html',
                {
                    'igreja': igreja,
                }
            )

        permissao = {
            'fechamento_mensal_view': 'financeiro.view_fechamentofinanceiromensal',
            'fechamento_confirmar_view': 'financeiro.fechar_mes',
            'fechamento_reabrir_view': 'financeiro.reabrir_mes',
            'fechamento_configurar_saldo_inicial_view': 'financeiro.configurar_saldo_inicial',
            'fechamento_reprocessar_view': 'financeiro.reabrir_mes',
            'financeiro_dashboard_view': 'financeiro.view_lancamentofinanceiro',
            'resumo_anual_excel_view': 'financeiro.view_lancamentofinanceiro',
            'entrada_list_view': 'financeiro.view_lancamentofinanceiro',
            'entrada_create_view': 'financeiro.add_lancamentofinanceiro',
            'entrada_update_view': 'financeiro.change_lancamentofinanceiro',
            'entrada_delete_view': 'financeiro.delete_lancamentofinanceiro',
            'categoria_entrada_list_view': 'financeiro.view_categoriafinanceira',
            'categoria_entrada_create_view': 'financeiro.add_categoriafinanceira',
            'categoria_entrada_update_view': 'financeiro.change_categoriafinanceira',
            'categoria_entrada_delete_view': 'financeiro.delete_categoriafinanceira',
            'conta_pagar_list_view': 'financeiro.view_lancamentofinanceiro',
            'conta_pagar_create_view': 'financeiro.add_lancamentofinanceiro',
            'despesa_recorrente_create_view': 'financeiro.add_lancamentofinanceiro',
            'conta_pagar_update_view': 'financeiro.change_lancamentofinanceiro',
            'conta_pagar_delete_view': 'financeiro.delete_lancamentofinanceiro',
            'categoria_saida_list_view': 'financeiro.view_categoriafinanceira',
            'categoria_saida_create_view': 'financeiro.add_categoriafinanceira',
            'categoria_saida_update_view': 'financeiro.change_categoriafinanceira',
            'categoria_saida_delete_view': 'financeiro.delete_categoriafinanceira',
        }.get(view_func.__name__)

        if permissao and not request.user.has_perm(permissao):
            messages.error(request, 'Você não possui permissão para acessar esta função.')
            return redirect('dashboard')

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapped


def get_resumo_anual_financeiro(igreja, ano):
    totais_por_mes = {
        mes: {
            LancamentoFinanceiro.TIPO_ENTRADA: Decimal('0'),
            LancamentoFinanceiro.TIPO_SAIDA: Decimal('0'),
        }
        for mes, label in MESES_ANO
    }

    totais_anuais = LancamentoFinanceiro.objects.filter(
        igreja=igreja,
        data__year=ano
    ).annotate(
        mes=ExtractMonth('data')
    ).values(
        'mes',
        'tipo'
    ).annotate(
        total=Sum('valor')
    )

    for item in totais_anuais:
        totais_por_mes[item['mes']][item['tipo']] = item['total'] or Decimal('0')

    resumo_anual = []

    for mes, label in MESES_ANO:
        receita = totais_por_mes[mes][LancamentoFinanceiro.TIPO_ENTRADA]
        despesa = totais_por_mes[mes][LancamentoFinanceiro.TIPO_SAIDA]

        resumo_anual.append(
            {
                'mes': label,
                'receita': receita,
                'despesa': despesa,
                'saldo': receita - despesa,
            }
        )

    return resumo_anual


def get_ano_dashboard(request):
    ano_atual = timezone.localdate().year
    ano_parametro = request.GET.get('ano')

    try:
        ano = int(ano_parametro) if ano_parametro else ano_atual
    except (TypeError, ValueError):
        ano = ano_atual

    return ano if 1 <= ano <= 9999 else ano_atual


def competencia_do_request(request):
    hoje = timezone.localdate()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
        return date(ano, mes, 1)
    except (TypeError, ValueError):
        return date(hoje.year, hoje.month, 1)


def competencia_anterior(competencia):
    return adicionar_meses(competencia, -1).replace(day=1)


def pode(request, permissao):
    return request.user.is_superuser or request.user.has_perm(f'financeiro.{permissao}')


def fechamento_do_mes(igreja, data_lancamento):
    return FechamentoFinanceiroMensal.objects.filter(
        igreja=igreja,
        competencia=data_lancamento.replace(day=1),
        status=FechamentoFinanceiroMensal.STATUS_FECHADO,
    ).first()


def lancamentos_do_periodo(igreja, competencia):
    proxima = adicionar_meses(competencia, 1)
    return LancamentoFinanceiro.objects.filter(
        igreja=igreja,
        data__gte=competencia,
        data__lt=proxima,
    ).select_related('categoria')


def totais_do_periodo(igreja, competencia):
    lancamentos = lancamentos_do_periodo(igreja, competencia)
    receitas = lancamentos.filter(tipo=LancamentoFinanceiro.TIPO_ENTRADA)
    despesas = lancamentos.filter(tipo=LancamentoFinanceiro.TIPO_SAIDA)
    total_receitas = receitas.aggregate(total=Sum('valor'))['total'] or Decimal('0')
    total_despesas = despesas.aggregate(total=Sum('valor'))['total'] or Decimal('0')
    return receitas, despesas, total_receitas, total_despesas


def saldo_inicial_da_competencia(igreja, competencia, fechamento=None):
    if fechamento:
        return fechamento.saldo_inicial, fechamento.origem_saldo_inicial
    anterior = FechamentoFinanceiroMensal.objects.filter(
        igreja=igreja,
        competencia__lt=competencia,
        status=FechamentoFinanceiroMensal.STATUS_FECHADO,
    ).order_by('-competencia').first()
    if anterior:
        return anterior.saldo_final, FechamentoFinanceiroMensal.ORIGEM_ANTERIOR
    return None, FechamentoFinanceiroMensal.ORIGEM_IMPLANTACAO


def bloquear_lancamento_em_mes_fechado(request, igreja, data_lancamento):
    if data_lancamento and fechamento_do_mes(igreja, data_lancamento):
        messages.error(request, 'Esta competência está fechada. Reabra o mês antes de alterar lançamentos.')
        return True
    return False


def build_resumo_anual_xlsx(igreja, ano, resumo_anual):
    rows = [
        [f'Totalizados do ano atual - {igreja.nome}'],
        ['Ano', *[item['mes'] for item in resumo_anual]],
        ['Despesas', *[item['despesa'] for item in resumo_anual]],
        ['Receita', *[item['receita'] for item in resumo_anual]],
        ['Saldo', *[item['saldo'] for item in resumo_anual]],
    ]
    rows[1][0] = str(ano)

    def cell_ref(column_index, row_index):
        return f'{ascii_uppercase[column_index]}{row_index}'

    def cell_xml(value, column_index, row_index):
        ref = cell_ref(column_index, row_index)

        if isinstance(value, Decimal):
            return f'<c r="{ref}" s="1"><v>{value}</v></c>'

        if isinstance(value, int):
            return f'<c r="{ref}"><v>{value}</v></c>'

        return (
            f'<c r="{ref}" t="inlineStr">'
            f'<is><t>{escape(str(value))}</t></is>'
            f'</c>'
        )

    sheet_rows = []

    for row_index, row in enumerate(rows, start=1):
        cells = ''.join(
            cell_xml(value, column_index, row_index)
            for column_index, value in enumerate(row)
        )
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')

    worksheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <cols>
        <col min="1" max="1" width="28" customWidth="1"/>
        <col min="2" max="13" width="14" customWidth="1"/>
    </cols>
    <sheetData>
        {''.join(sheet_rows)}
    </sheetData>
</worksheet>'''

    output = BytesIO()

    with ZipFile(output, 'w', ZIP_DEFLATED) as xlsx:
        xlsx.writestr(
            '[Content_Types].xml',
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
    <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''
        )
        xlsx.writestr(
            '_rels/.rels',
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
        )
        xlsx.writestr(
            'xl/workbook.xml',
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets>
        <sheet name="Resumo anual" sheetId="1" r:id="rId1"/>
    </sheets>
</workbook>'''
        )
        xlsx.writestr(
            'xl/_rels/workbook.xml.rels',
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''
        )
        xlsx.writestr(
            'xl/styles.xml',
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
    <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
    <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
    <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
    <cellXfs count="2">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
        <xf numFmtId="4" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
    </cellXfs>
    <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''
        )
        xlsx.writestr('xl/worksheets/sheet1.xml', worksheet)

    output.seek(0)
    return output


@login_required
@plano_financeiro_required
def fechamento_mensal_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')

    competencia = competencia_do_request(request)
    fechamento = FechamentoFinanceiroMensal.objects.filter(igreja=igreja, competencia=competencia).first()
    receitas, despesas, total_receitas, total_despesas = totais_do_periodo(igreja, competencia)
    saldo_inicial, origem = saldo_inicial_da_competencia(igreja, competencia, fechamento)
    saldo_inicial = saldo_inicial if saldo_inicial is not None else Decimal('0')
    total_disponivel = saldo_inicial + total_receitas
    saldo_final = total_disponivel - total_despesas
    posteriores = FechamentoFinanceiroMensal.objects.filter(igreja=igreja, competencia__gt=competencia, status=FechamentoFinanceiroMensal.STATUS_FECHADO).exists()
    meses = list(enumerate(MESES_ANO_EXTENSO, 1))
    anos_lancamentos = [item.year for item in LancamentoFinanceiro.objects.filter(igreja=igreja).dates('data', 'year')]
    anos_fechamentos = [item.year for item in FechamentoFinanceiroMensal.objects.filter(igreja=igreja).dates('competencia', 'year')]
    anos = sorted(set([competencia.year, *anos_lancamentos, *anos_fechamentos]), reverse=True)
    historico_fechamentos = FechamentoFinanceiroMensal.objects.filter(igreja=igreja).order_by('-competencia')
    return render(request, 'financeiro/fechamento_mensal.html', {
        'igreja': igreja, 'competencia': competencia, 'fechamento': fechamento,
        'receitas': receitas, 'despesas': despesas, 'total_receitas': total_receitas,
        'total_despesas': total_despesas, 'saldo_inicial': saldo_inicial,
        'origem_saldo_inicial': origem, 'total_disponivel': total_disponivel,
        'saldo_final': saldo_final, 'meses': meses, 'anos': anos,
        'pode_fechar': pode(request, 'fechar_mes'), 'pode_reabrir': pode(request, 'reabrir_mes'),
        'pode_configurar_saldo': pode(request, 'configurar_saldo_inicial'),
        'possui_posteriores_fechados': posteriores,
        'historico_fechamentos': historico_fechamentos,
        'competencia_display': f'{MESES_ANO_EXTENSO[competencia.month - 1]}/{competencia.year}',
    })


@login_required
@plano_financeiro_required
def fechamento_confirmar_view(request):
    if request.method != 'POST':
        return redirect('financeiro_fechamento_mensal')
    igreja = get_igreja_selecionada(request)
    if igreja is None or not pode(request, 'fechar_mes'):
        messages.error(request, 'Você não tem permissão para fechar competências.')
        return redirect('financeiro_fechamento_mensal')
    try:
        competencia = date(int(request.POST['ano']), int(request.POST['mes']), 1)
    except (KeyError, TypeError, ValueError):
        messages.error(request, 'Competência inválida.')
        return redirect('financeiro_fechamento_mensal')
    with transaction.atomic():
        fechamento = FechamentoFinanceiroMensal.objects.select_for_update().filter(igreja=igreja, competencia=competencia).first()
        if fechamento and fechamento.status == FechamentoFinanceiroMensal.STATUS_FECHADO:
            messages.error(request, 'Esta competência já está fechada.')
            return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={competencia.year}&mes={competencia.month}')
        saldo_inicial, origem = saldo_inicial_da_competencia(igreja, competencia, fechamento)
        if saldo_inicial is None:
            if not pode(request, 'configurar_saldo_inicial'):
                messages.error(request, 'Informe o saldo inicial de implantação por um usuário autorizado.')
                return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={competencia.year}&mes={competencia.month}')
            try:
                saldo_inicial = Decimal(request.POST['saldo_inicial'])
            except Exception:
                messages.error(request, 'Informe um saldo inicial válido para o primeiro fechamento.')
                return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={competencia.year}&mes={competencia.month}')
            origem = FechamentoFinanceiroMensal.ORIGEM_IMPLANTACAO
        _, _, receitas, despesas = totais_do_periodo(igreja, competencia)
        fechamento, _ = FechamentoFinanceiroMensal.objects.update_or_create(
            igreja=igreja, competencia=competencia,
            defaults={
                'saldo_inicial': saldo_inicial, 'origem_saldo_inicial': origem,
                'total_receitas': receitas, 'total_despesas': despesas,
                'saldo_final': saldo_inicial + receitas - despesas,
                'status': FechamentoFinanceiroMensal.STATUS_FECHADO,
                'fechado_em': timezone.now(), 'fechado_por': request.user,
            }
        )
    messages.success(request, f'Competência {competencia:%m/%Y} fechada com sucesso.')
    return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={competencia.year}&mes={competencia.month}')


@login_required
@plano_financeiro_required
def fechamento_reabrir_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if request.method != 'POST' or igreja is None or not pode(request, 'reabrir_mes'):
        messages.error(request, 'Você não tem permissão para reabrir competências.')
        return redirect('financeiro_fechamento_mensal')
    fechamento = get_object_or_404(FechamentoFinanceiroMensal, pk=pk, igreja=igreja)
    fechamento.status = FechamentoFinanceiroMensal.STATUS_ABERTO
    fechamento.reaberto_em = timezone.now()
    fechamento.reaberto_por = request.user
    fechamento.save(update_fields=['status', 'reaberto_em', 'reaberto_por', 'updated_at'])
    messages.warning(request, 'Competência reaberta. Recalcule as competências posteriores após qualquer alteração.')
    return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={fechamento.competencia.year}&mes={fechamento.competencia.month}')


@login_required
@plano_financeiro_required
def fechamento_configurar_saldo_inicial_view(request, pk):
    """Operação administrativa para corrigir a implantação sem criar lançamentos."""
    igreja = get_igreja_selecionada(request)
    if request.method != 'POST' or igreja is None or not pode(request, 'configurar_saldo_inicial'):
        messages.error(request, 'Você não tem permissão para configurar o saldo inicial.')
        return redirect('financeiro_fechamento_mensal')
    fechamento = get_object_or_404(
        FechamentoFinanceiroMensal,
        pk=pk,
        igreja=igreja,
        status=FechamentoFinanceiroMensal.STATUS_ABERTO,
        origem_saldo_inicial=FechamentoFinanceiroMensal.ORIGEM_IMPLANTACAO,
    )
    if FechamentoFinanceiroMensal.objects.filter(igreja=igreja, competencia__gt=fechamento.competencia, status=FechamentoFinanceiroMensal.STATUS_FECHADO).exists():
        messages.error(request, 'Existem competências posteriores fechadas. Reabra-as antes de alterar a implantação.')
        return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={fechamento.competencia.year}&mes={fechamento.competencia.month}')
    try:
        saldo_inicial = Decimal(request.POST['saldo_inicial'])
    except Exception:
        messages.error(request, 'Informe um saldo inicial válido.')
        return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={fechamento.competencia.year}&mes={fechamento.competencia.month}')
    _, _, receitas, despesas = totais_do_periodo(igreja, fechamento.competencia)
    fechamento.saldo_inicial = saldo_inicial
    fechamento.total_receitas = receitas
    fechamento.total_despesas = despesas
    fechamento.saldo_final = saldo_inicial + receitas - despesas
    fechamento.save(update_fields=['saldo_inicial', 'total_receitas', 'total_despesas', 'saldo_final', 'updated_at'])
    messages.success(request, 'Saldo inicial de implantação atualizado.')
    return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={fechamento.competencia.year}&mes={fechamento.competencia.month}')


@login_required
@plano_financeiro_required
def fechamento_reprocessar_view(request, pk):
    igreja = get_igreja_selecionada(request)
    if request.method != 'POST' or igreja is None or not pode(request, 'fechar_mes'):
        messages.error(request, 'Você não tem permissão para reprocessar competências.')
        return redirect('financeiro_fechamento_mensal')
    base = get_object_or_404(FechamentoFinanceiroMensal, pk=pk, igreja=igreja)
    anteriores = FechamentoFinanceiroMensal.objects.filter(igreja=igreja, competencia__gte=base.competencia).order_by('competencia')
    anterior = FechamentoFinanceiroMensal.objects.filter(igreja=igreja, competencia__lt=base.competencia, status=FechamentoFinanceiroMensal.STATUS_FECHADO).order_by('-competencia').first()
    for fechamento in anteriores:
        if fechamento.status != FechamentoFinanceiroMensal.STATUS_FECHADO:
            continue
        if anterior:
            fechamento.saldo_inicial = anterior.saldo_final
            fechamento.origem_saldo_inicial = FechamentoFinanceiroMensal.ORIGEM_ANTERIOR
        _, _, receitas, despesas = totais_do_periodo(igreja, fechamento.competencia)
        fechamento.total_receitas, fechamento.total_despesas = receitas, despesas
        fechamento.saldo_final = fechamento.saldo_inicial + receitas - despesas
        fechamento.save(update_fields=['saldo_inicial', 'origem_saldo_inicial', 'total_receitas', 'total_despesas', 'saldo_final', 'updated_at'])
        anterior = fechamento
    messages.success(request, 'Saldos das competências fechadas foram reprocessados.')
    return redirect(f'{redirect("financeiro_fechamento_mensal").url}?ano={base.competencia.year}&mes={base.competencia.month}')


@login_required
@plano_financeiro_required
def financeiro_dashboard_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    ano_selecionado = get_ano_dashboard(request)
    lancamentos = LancamentoFinanceiro.objects.filter(
        igreja=igreja,
        data__year=ano_selecionado
    )

    total_entradas = lancamentos.filter(
        tipo=LancamentoFinanceiro.TIPO_ENTRADA
    ).aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0')

    total_despesas = lancamentos.filter(
        tipo=LancamentoFinanceiro.TIPO_SAIDA
    ).aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0')

    saldo = total_entradas - total_despesas

    anos_disponiveis = list(
        LancamentoFinanceiro.objects.filter(igreja=igreja).dates(
            'data',
            'year',
            order='DESC'
        )
    )
    anos_disponiveis = [data.year for data in anos_disponiveis]
    if ano_selecionado not in anos_disponiveis:
        anos_disponiveis.append(ano_selecionado)
        anos_disponiveis.sort(reverse=True)

    resumo_anual = get_resumo_anual_financeiro(igreja, ano_selecionado)

    return render(
        request,
        'financeiro/dashboard.html',
        {
            'igreja': igreja,
            'total_entradas': total_entradas,
            'total_despesas': total_despesas,
            'saldo': saldo,
            'ano_selecionado': ano_selecionado,
            'anos_disponiveis': anos_disponiveis,
            'resumo_anual': resumo_anual,
        }
    )


@login_required
@plano_financeiro_required
def resumo_anual_excel_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    ano_selecionado = get_ano_dashboard(request)
    resumo_anual = get_resumo_anual_financeiro(igreja, ano_selecionado)
    output = build_resumo_anual_xlsx(
        igreja,
        ano_selecionado,
        resumo_anual
    )

    filename = f'resumo-financeiro-{ano_selecionado}.xlsx'
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
@plano_financeiro_required
def entrada_list_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    pesquisa = request.GET.get('q', '').strip()
    entradas = LancamentoFinanceiro.objects.select_related(
        'categoria',
        'membro'
    ).filter(
        igreja=igreja,
        tipo=LancamentoFinanceiro.TIPO_ENTRADA
    )

    if pesquisa:
        entradas = entradas.filter(
            descricao__icontains=pesquisa
        )

    total_entradas = entradas.aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0')

    return render(
        request,
        'financeiro/entrada_list.html',
        {
            'igreja': igreja,
            'entradas': entradas,
            'pesquisa': pesquisa,
            'total_entradas': total_entradas,
        }
    )


@login_required
@plano_financeiro_required
def entrada_create_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    form = EntradaFinanceiraForm(
        request.POST or None,
        igreja=igreja
    )

    if request.method == 'POST' and form.is_valid():
        entrada = form.save(commit=False)
        if bloquear_lancamento_em_mes_fechado(request, igreja, entrada.data):
            return redirect('financeiro_entrada_list')
        entrada.igreja = igreja
        entrada.tipo = LancamentoFinanceiro.TIPO_ENTRADA
        entrada.save()

        return redirect('financeiro_entrada_list')

    return render(
        request,
        'financeiro/entrada_form.html',
        {
            'form': form,
            'igreja': igreja,
            'titulo': 'Nova entrada',
        }
    )


@login_required
@plano_financeiro_required
def entrada_update_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    entrada = get_object_or_404(
        LancamentoFinanceiro,
        pk=pk,
        igreja=igreja,
        tipo=LancamentoFinanceiro.TIPO_ENTRADA
    )
    data_original = entrada.data

    form = EntradaFinanceiraForm(
        request.POST or None,
        instance=entrada,
        igreja=igreja
    )

    if request.method == 'POST' and form.is_valid():
        entrada = form.save(commit=False)
        if (bloquear_lancamento_em_mes_fechado(request, igreja, data_original)
                or bloquear_lancamento_em_mes_fechado(request, igreja, entrada.data)):
            return redirect('financeiro_entrada_list')
        entrada.igreja = igreja
        entrada.tipo = LancamentoFinanceiro.TIPO_ENTRADA
        entrada.save()

        return redirect('financeiro_entrada_list')

    return render(
        request,
        'financeiro/entrada_form.html',
        {
            'form': form,
            'igreja': igreja,
            'entrada': entrada,
            'titulo': 'Editar entrada',
        }
    )


@login_required
@plano_financeiro_required
def entrada_delete_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    entrada = get_object_or_404(
        LancamentoFinanceiro,
        pk=pk,
        igreja=igreja,
        tipo=LancamentoFinanceiro.TIPO_ENTRADA
    )

    if request.method == 'POST':
        if bloquear_lancamento_em_mes_fechado(request, igreja, entrada.data):
            return redirect('financeiro_entrada_list')
        entrada.delete()

        return redirect('financeiro_entrada_list')

    return render(
        request,
        'financeiro/entrada_confirm_delete.html',
        {
            'igreja': igreja,
            'entrada': entrada,
        }
    )


@login_required
@plano_financeiro_required
def categoria_entrada_list_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    categorias = CategoriaFinanceira.objects.filter(
        igreja=igreja,
        tipo=CategoriaFinanceira.TIPO_ENTRADA
    )

    return render(
        request,
        'financeiro/categoria_entrada_list.html',
        {
            'igreja': igreja,
            'categorias': categorias,
        }
    )


@login_required
@plano_financeiro_required
def categoria_entrada_create_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    form = CategoriaEntradaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        categoria = form.save(commit=False)
        categoria.igreja = igreja
        categoria.tipo = CategoriaFinanceira.TIPO_ENTRADA
        categoria.save()

        return redirect('financeiro_categoria_entrada_list')

    return render(
        request,
        'financeiro/categoria_entrada_form.html',
        {
            'form': form,
            'igreja': igreja,
            'titulo': 'Nova categoria de entrada',
        }
    )


@login_required
@plano_financeiro_required
def categoria_entrada_update_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    categoria = get_object_or_404(
        CategoriaFinanceira,
        pk=pk,
        igreja=igreja,
        tipo=CategoriaFinanceira.TIPO_ENTRADA
    )

    form = CategoriaEntradaForm(
        request.POST or None,
        instance=categoria
    )

    if request.method == 'POST' and form.is_valid():
        categoria = form.save(commit=False)
        categoria.igreja = igreja
        categoria.tipo = CategoriaFinanceira.TIPO_ENTRADA
        categoria.save()

        return redirect('financeiro_categoria_entrada_list')

    return render(
        request,
        'financeiro/categoria_entrada_form.html',
        {
            'form': form,
            'igreja': igreja,
            'categoria': categoria,
            'titulo': 'Editar categoria de entrada',
        }
    )


@login_required
@plano_financeiro_required
def categoria_entrada_delete_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    categoria = get_object_or_404(
        CategoriaFinanceira,
        pk=pk,
        igreja=igreja,
        tipo=CategoriaFinanceira.TIPO_ENTRADA
    )

    if request.method == 'POST':
        try:
            categoria.delete()
        except ProtectedError:
            messages.error(
                request,
                'Esta categoria não pode ser excluída porque possui entradas vinculadas.'
            )
        else:
            messages.success(request, 'Categoria de entrada excluída com sucesso.')

        return redirect('financeiro_categoria_entrada_list')

    return render(
        request,
        'financeiro/categoria_entrada_confirm_delete.html',
        {'igreja': igreja, 'categoria': categoria}
    )


@login_required
@plano_financeiro_required
def conta_pagar_list_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    pesquisa = request.GET.get('q', '').strip()
    contas = LancamentoFinanceiro.objects.select_related(
        'categoria'
    ).filter(
        igreja=igreja,
        tipo=LancamentoFinanceiro.TIPO_SAIDA
    )

    if pesquisa:
        contas = contas.filter(
            descricao__icontains=pesquisa
        )

    total_contas = contas.aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0')

    return render(
        request,
        'financeiro/conta_pagar_list.html',
        {
            'igreja': igreja,
            'contas': contas,
            'pesquisa': pesquisa,
            'total_contas': total_contas,
        }
    )


@login_required
@plano_financeiro_required
def conta_pagar_create_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    form = ContaPagarForm(
        request.POST or None,
        igreja=igreja
    )

    if request.method == 'POST' and form.is_valid():
        conta = form.save(commit=False)
        if bloquear_lancamento_em_mes_fechado(request, igreja, conta.data):
            return redirect('financeiro_conta_pagar_list')
        conta.igreja = igreja
        conta.tipo = LancamentoFinanceiro.TIPO_SAIDA
        conta.save()

        return redirect('financeiro_conta_pagar_list')

    return render(
        request,
        'financeiro/conta_pagar_form.html',
        {
            'form': form,
            'igreja': igreja,
            'titulo': 'Nova conta a pagar',
        }
    )


@login_required
@plano_financeiro_required
def despesa_recorrente_create_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    form = DespesaRecorrenteForm(
        request.POST or None,
        igreja=igreja
    )

    if request.method == 'POST' and form.is_valid():
        dados = form.cleaned_data
        grupo_recorrencia = uuid.uuid4()
        quantidade = dados['quantidade']
        parcelada = (
            dados['tipo_geracao']
            == DespesaRecorrenteForm.TIPO_PARCELADA
        )
        lancamentos = []

        for indice in range(quantidade):
            numero = indice + 1
            descricao = dados['descricao']

            if parcelada:
                descricao = f'{descricao} - Parcela {numero}/{quantidade}'

            lancamentos.append(
                LancamentoFinanceiro(
                    igreja=igreja,
                    tipo=LancamentoFinanceiro.TIPO_SAIDA,
                    data_emissao=timezone.localdate(),
                    data=adicionar_meses(
                        dados['data_primeiro_vencimento'],
                        indice
                    ),
                    categoria=dados['categoria'],
                    descricao=descricao,
                    valor=dados['valor_parcela'],
                    forma_pagamento=dados['forma_pagamento'],
                    observacao=dados['observacao'],
                    grupo_recorrencia=grupo_recorrencia,
                    numero_parcela=numero,
                    total_parcelas=quantidade,
                )
            )

        if any(bloquear_lancamento_em_mes_fechado(request, igreja, item.data) for item in lancamentos):
            return redirect('financeiro_conta_pagar_list')

        with transaction.atomic():
            LancamentoFinanceiro.objects.bulk_create(lancamentos)

        return redirect('financeiro_conta_pagar_list')

    return render(
        request,
        'financeiro/despesa_recorrente_form.html',
        {
            'form': form,
            'igreja': igreja,
        }
    )


@login_required
@plano_financeiro_required
def conta_pagar_update_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    conta = get_object_or_404(
        LancamentoFinanceiro,
        pk=pk,
        igreja=igreja,
        tipo=LancamentoFinanceiro.TIPO_SAIDA
    )
    data_original = conta.data

    form = ContaPagarForm(
        request.POST or None,
        instance=conta,
        igreja=igreja
    )

    if request.method == 'POST' and form.is_valid():
        conta = form.save(commit=False)
        if (bloquear_lancamento_em_mes_fechado(request, igreja, data_original)
                or bloquear_lancamento_em_mes_fechado(request, igreja, conta.data)):
            return redirect('financeiro_conta_pagar_list')
        conta.igreja = igreja
        conta.tipo = LancamentoFinanceiro.TIPO_SAIDA
        conta.save()

        return redirect('financeiro_conta_pagar_list')

    return render(
        request,
        'financeiro/conta_pagar_form.html',
        {
            'form': form,
            'igreja': igreja,
            'conta': conta,
            'titulo': 'Editar conta a pagar',
        }
    )


@login_required
@plano_financeiro_required
def conta_pagar_delete_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    conta = get_object_or_404(
        LancamentoFinanceiro,
        pk=pk,
        igreja=igreja,
        tipo=LancamentoFinanceiro.TIPO_SAIDA
    )

    if request.method == 'POST':
        if bloquear_lancamento_em_mes_fechado(request, igreja, conta.data):
            return redirect('financeiro_conta_pagar_list')
        conta.delete()

        return redirect('financeiro_conta_pagar_list')

    return render(
        request,
        'financeiro/conta_pagar_confirm_delete.html',
        {
            'igreja': igreja,
            'conta': conta,
        }
    )


@login_required
@plano_financeiro_required
def categoria_saida_list_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    categorias = CategoriaFinanceira.objects.filter(
        igreja=igreja,
        tipo=CategoriaFinanceira.TIPO_SAIDA
    )

    return render(
        request,
        'financeiro/categoria_saida_list.html',
        {
            'igreja': igreja,
            'categorias': categorias,
        }
    )


@login_required
@plano_financeiro_required
def categoria_saida_create_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    form = CategoriaSaidaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        categoria = form.save(commit=False)
        categoria.igreja = igreja
        categoria.tipo = CategoriaFinanceira.TIPO_SAIDA
        categoria.save()

        return redirect('financeiro_categoria_saida_list')

    return render(
        request,
        'financeiro/categoria_saida_form.html',
        {
            'form': form,
            'igreja': igreja,
            'titulo': 'Nova categoria de saida',
        }
    )


@login_required
@plano_financeiro_required
def categoria_saida_update_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    categoria = get_object_or_404(
        CategoriaFinanceira,
        pk=pk,
        igreja=igreja,
        tipo=CategoriaFinanceira.TIPO_SAIDA
    )

    form = CategoriaSaidaForm(
        request.POST or None,
        instance=categoria
    )

    if request.method == 'POST' and form.is_valid():
        categoria = form.save(commit=False)
        categoria.igreja = igreja
        categoria.tipo = CategoriaFinanceira.TIPO_SAIDA
        categoria.save()

        return redirect('financeiro_categoria_saida_list')

    return render(
        request,
        'financeiro/categoria_saida_form.html',
        {
            'form': form,
            'igreja': igreja,
            'categoria': categoria,
            'titulo': 'Editar categoria de saida',
        }
    )


@login_required
@plano_financeiro_required
def categoria_saida_delete_view(request, pk):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    categoria = get_object_or_404(
        CategoriaFinanceira,
        pk=pk,
        igreja=igreja,
        tipo=CategoriaFinanceira.TIPO_SAIDA
    )

    if request.method == 'POST':
        try:
            categoria.delete()
        except ProtectedError:
            messages.error(
                request,
                'Esta categoria não pode ser excluída porque possui contas a pagar vinculadas.'
            )
        else:
            messages.success(request, 'Categoria de saída excluída com sucesso.')

        return redirect('financeiro_categoria_saida_list')

    return render(
        request,
        'financeiro/categoria_saida_confirm_delete.html',
        {'igreja': igreja, 'categoria': categoria}
    )
