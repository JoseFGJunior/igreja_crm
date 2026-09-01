from datetime import timedelta
from io import BytesIO
from string import ascii_uppercase
from xml.sax.saxutils import escape
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from urllib.parse import quote

from apps.accounts.models import UsuarioIgreja
from apps.core.models import AcaoMissionaria
from apps.core.models import MensagemAniversario
from apps.core.forms import MensagemAniversarioForm
from apps.membros.models import Membro
from apps.membros.models import AcompanhamentoVisitante
from apps.membros.services import normalizar_whatsapp


def home_view(request):
    acoes_missionarias = AcaoMissionaria.objects.filter(
        ativo=True
    )[:6]

    return render(
        request,
        'site/home.html',
        {
            'acoes_missionarias': acoes_missionarias,
        }
    )


FAIXAS_ETARIAS = [
    {
        'nome': 'Bebes',
        'idade': '0 a 4 anos',
        'minimo': 0,
        'maximo': 4,
    },
    {
        'nome': 'Criancas',
        'idade': '5 a 12 anos',
        'minimo': 5,
        'maximo': 12,
    },
    {
        'nome': 'Adolescentes',
        'idade': '13 a 17 anos',
        'minimo': 13,
        'maximo': 17,
    },
    {
        'nome': 'Jovens',
        'idade': '18 a 35 anos',
        'minimo': 18,
        'maximo': 35,
    },
    {
        'nome': 'Adultos',
        'idade': '40 a 55 anos',
        'minimo': 40,
        'maximo': 55,
    },
    {
        'nome': 'Idosos',
        'idade': '65 anos ou mais',
        'minimo': 65,
        'maximo': None,
    },
]


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


def get_aniversariantes_semana(membros, hoje):
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    dias_semana = set()
    dia_atual = inicio_semana

    while dia_atual <= fim_semana:
        dias_semana.add(
            (
                dia_atual.month,
                dia_atual.day
            )
        )
        dia_atual += timedelta(days=1)

    aniversariantes = [
        membro
        for membro in membros
        if membro.data_nascimento
        and (
            membro.data_nascimento.month,
            membro.data_nascimento.day
        ) in dias_semana
    ]

    return sorted(
        aniversariantes,
        key=lambda membro: (
            membro.data_nascimento.month,
            membro.data_nascimento.day,
            membro.nome
        )
    )


def calcular_idade(data_nascimento, hoje):
    idade = hoje.year - data_nascimento.year

    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1

    return idade


def get_faixa_etaria(idade):
    for faixa in FAIXAS_ETARIAS:
        idade_maxima = faixa['maximo']

        if idade >= faixa['minimo'] and (
            idade_maxima is None or idade <= idade_maxima
        ):
            return faixa

    return {
        'nome': 'Outras faixas',
        'idade': '36 a 39 anos e 56 a 64 anos',
    }


def get_resumo_faixa_etaria(membros, hoje):
    faixas = [
        {
            **faixa,
            'total': 0,
        }
        for faixa in FAIXAS_ETARIAS
    ]
    outras_faixas = 0
    sem_data_nascimento = 0

    for membro in membros:
        if not membro.data_nascimento:
            sem_data_nascimento += 1
            continue

        idade = calcular_idade(
            membro.data_nascimento,
            hoje
        )
        faixa_encontrada = False

        for faixa in faixas:
            idade_maxima = faixa['maximo']

            if idade >= faixa['minimo'] and (
                idade_maxima is None or idade <= idade_maxima
            ):
                faixa['total'] += 1
                faixa_encontrada = True
                break

        if not faixa_encontrada:
            outras_faixas += 1

    return faixas, outras_faixas, sem_data_nascimento


def build_xlsx(rows, sheet_name='Planilha'):
    def cell_ref(column_index, row_index):
        column_name = ''
        index = column_index

        while True:
            column_name = ascii_uppercase[index % 26] + column_name
            index = index // 26 - 1

            if index < 0:
                break

        return f'{column_name}{row_index}'

    def cell_xml(value, column_index, row_index):
        ref = cell_ref(column_index, row_index)

        if isinstance(value, int):
            return f'<c r="{ref}"><v>{value}</v></c>'

        return (
            f'<c r="{ref}" t="inlineStr">'
            f'<is><t>{escape(str(value or ""))}</t></is>'
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
            f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets>
        <sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/>
    </sheets>
</workbook>'''
        )
        xlsx.writestr(
            'xl/_rels/workbook.xml.rels',
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''
        )
        xlsx.writestr('xl/worksheets/sheet1.xml', worksheet)

    output.seek(0)
    return output


def excel_response(rows, filename, sheet_name='Planilha'):
    output = build_xlsx(
        rows,
        sheet_name=sheet_name
    )
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
def dashboard_view(request):
    igrejas_usuario = UsuarioIgreja.objects.select_related('igreja').filter(
        usuario=request.user,
        ativo=True,
        igreja__ativa=True
    ).order_by(
        '-igreja_default',
        'igreja__nome'
    )

    igreja_id = request.session.get('igreja_id')

    igreja_selecionada = None

    if igreja_id:
        igreja_selecionada = igrejas_usuario.filter(
            igreja_id=igreja_id
        ).first()

    if igreja_selecionada is None:
        igreja_selecionada = igrejas_usuario.first()

        if igreja_selecionada:
            request.session['igreja_id'] = igreja_selecionada.igreja_id

    total_membros = 0
    total_visitantes = 0
    total_congregados = 0
    aniversariantes_mes = []
    aniversariantes_semana = []
    resumo_faixa_etaria = []
    outras_faixas_etarias = 0
    sem_data_nascimento = 0
    grafico_faixa_etaria_labels = []
    grafico_faixa_etaria_totais = []
    visitantes_para_acompanhar_hoje = 0
    visitantes_para_acompanhar_atrasados = 0
    aniversariantes_hoje = []
    mensagem_aniversario = None

    pode_visualizar_membros = request.user.has_perm('membros.view_membro')

    if igreja_selecionada and pode_visualizar_membros:
        membros = Membro.objects.filter(
            igreja=igreja_selecionada.igreja
        )
        hoje = timezone.localdate()

        total_membros = membros.filter(status='MEMBRO').count()
        total_visitantes = membros.filter(status='VISITANTE').count()
        total_congregados = membros.filter(status='CONGREGADO').count()
        membros_com_nascimento = list(membros.exclude(data_nascimento__isnull=True))

        aniversariantes_mes = sorted(
            [
                membro
                for membro in membros_com_nascimento
                if membro.data_nascimento.month == hoje.month
            ],
            key=lambda membro: (
                membro.data_nascimento.day,
                membro.nome
            )
        )

        aniversariantes_hoje = [
            membro for membro in membros_com_nascimento
            if (
                membro.data_nascimento.month == hoje.month
                and membro.data_nascimento.day == hoje.day
            )
        ]
        mensagem_aniversario, _ = MensagemAniversario.objects.get_or_create(
            igreja=igreja_selecionada.igreja
        )
        if mensagem_aniversario.ativa:
            for aniversariante in aniversariantes_hoje:
                texto = mensagem_aniversario.texto.replace(
                    '{nome}', aniversariante.nome
                )
                if mensagem_aniversario.versiculo:
                    texto = f'{texto}\n\n📖 {mensagem_aniversario.versiculo}'
                texto = f'{texto}\n\n{igreja_selecionada.igreja.nome}'
                if aniversariante.telefone:
                    aniversariante.whatsapp_url = (
                        f'https://wa.me/{normalizar_whatsapp(aniversariante.telefone)}'
                        f'?text={quote(texto)}'
                    )

        aniversariantes_semana = get_aniversariantes_semana(
            membros_com_nascimento,
            hoje
        )
        (
            resumo_faixa_etaria,
            outras_faixas_etarias,
            sem_data_nascimento,
        ) = get_resumo_faixa_etaria(
            membros,
            hoje
        )
        grafico_faixa_etaria_labels = [
            faixa['nome']
            for faixa in resumo_faixa_etaria
        ]
        grafico_faixa_etaria_totais = [
            faixa['total']
            for faixa in resumo_faixa_etaria
        ]

        acompanhamentos = AcompanhamentoVisitante.objects.filter(
            igreja=igreja_selecionada.igreja,
            status='PENDENTE',
        )
        visitantes_para_acompanhar_hoje = acompanhamentos.filter(
            data_prevista=hoje
        ).count()
        visitantes_para_acompanhar_atrasados = acompanhamentos.filter(
            data_prevista__lt=hoje
        ).count()

        if outras_faixas_etarias:
            grafico_faixa_etaria_labels.append('Outras faixas')
            grafico_faixa_etaria_totais.append(outras_faixas_etarias)

        if sem_data_nascimento:
            grafico_faixa_etaria_labels.append('Sem data')
            grafico_faixa_etaria_totais.append(sem_data_nascimento)

    return render(
        request,
        'core/dashboard.html',
        {
            'igrejas_usuario': igrejas_usuario,
            'igreja_selecionada': igreja_selecionada,
            'total_membros': total_membros,
            'total_visitantes': total_visitantes,
            'total_congregados': total_congregados,
            'aniversariantes_mes': aniversariantes_mes,
            'aniversariantes_semana': aniversariantes_semana,
            'resumo_faixa_etaria': resumo_faixa_etaria,
            'outras_faixas_etarias': outras_faixas_etarias,
            'sem_data_nascimento': sem_data_nascimento,
            'grafico_faixa_etaria_labels': grafico_faixa_etaria_labels,
            'grafico_faixa_etaria_totais': grafico_faixa_etaria_totais,
            'pode_visualizar_membros': pode_visualizar_membros,
            'visitantes_para_acompanhar_hoje': visitantes_para_acompanhar_hoje,
            'visitantes_para_acompanhar_atrasados': visitantes_para_acompanhar_atrasados,
            'aniversariantes_hoje': aniversariantes_hoje,
            'mensagem_aniversario': mensagem_aniversario,
        }
    )


@login_required
@permission_required('membros.change_membro', raise_exception=True)
def aniversario_mensagem_view(request):
    igreja = get_igreja_selecionada(request)
    if igreja is None:
        return redirect('dashboard')
    mensagem, _ = MensagemAniversario.objects.get_or_create(igreja=igreja)
    form = MensagemAniversarioForm(request.POST or None, instance=mensagem)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'core/aniversario_mensagem.html', {
        'form': form,
        'igreja': igreja,
    })


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def exportar_faixa_etaria_excel_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    hoje = timezone.localdate()
    membros = Membro.objects.filter(
        igreja=igreja
    ).order_by(
        'nome'
    )

    rows = [
        [f'Membros por faixa etaria - {igreja.nome}'],
        ['Nome', 'Status', 'Data nascimento', 'Idade', 'Grupo', 'Faixa', 'Telefone', 'Email'],
    ]

    for membro in membros:
        data_nascimento = ''
        idade = ''
        grupo = 'Sem data de nascimento'
        faixa_descricao = 'Cadastro incompleto'

        if membro.data_nascimento:
            data_nascimento = membro.data_nascimento.strftime('%d/%m/%Y')
            idade = calcular_idade(
                membro.data_nascimento,
                hoje
            )
            faixa = get_faixa_etaria(idade)
            grupo = faixa['nome']
            faixa_descricao = faixa['idade']

        rows.append(
            [
                membro.nome,
                membro.get_status_display(),
                data_nascimento,
                idade,
                grupo,
                faixa_descricao,
                membro.telefone or '',
                membro.email or '',
            ]
        )

    return excel_response(
        rows,
        f'membros-faixa-etaria-{hoje:%Y%m%d}.xlsx',
        sheet_name='Faixa etaria'
    )


@login_required
@permission_required('membros.view_membro', raise_exception=True)
def exportar_visitantes_excel_view(request):
    igreja = get_igreja_selecionada(request)

    if igreja is None:
        return redirect('dashboard')

    hoje = timezone.localdate()
    visitantes = Membro.objects.filter(
        igreja=igreja,
        status='VISITANTE'
    ).order_by(
        'nome'
    )

    rows = [
        [f'Visitantes - {igreja.nome}'],
        ['Nome', 'Telefone', 'Email', 'Cidade', 'Bairro', 'Data nascimento', 'Idade'],
    ]

    for visitante in visitantes:
        data_nascimento = ''
        idade = ''

        if visitante.data_nascimento:
            data_nascimento = visitante.data_nascimento.strftime('%d/%m/%Y')
            idade = calcular_idade(
                visitante.data_nascimento,
                hoje
            )

        rows.append(
            [
                visitante.nome,
                visitante.telefone or '',
                visitante.email or '',
                visitante.cidade or '',
                visitante.bairro or '',
                data_nascimento,
                idade,
            ]
        )

    return excel_response(
        rows,
        f'visitantes-{hoje:%Y%m%d}.xlsx',
        sheet_name='Visitantes'
    )


@login_required
def selecionar_igreja_view(request):
    if request.method == 'POST':
        igreja_id = request.POST.get('igreja_id')

        usuario_igreja = UsuarioIgreja.objects.filter(
            usuario=request.user,
            igreja_id=igreja_id,
            ativo=True,
            igreja__ativa=True
        ).first()

        if usuario_igreja:
            request.session['igreja_id'] = usuario_igreja.igreja_id

    return redirect('dashboard')
