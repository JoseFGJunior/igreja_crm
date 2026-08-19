from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from apps.igrejas.models import Igreja
from apps.membros.models import Membro


EXCEL_EPOCH = date(1899, 12, 30)
XML_NS = {
    'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


class Command(BaseCommand):
    help = 'Importa membros de uma planilha XLSX para a igreja informada.'

    def add_arguments(self, parser):
        parser.add_argument(
            'arquivo',
            help='Caminho do arquivo XLSX.'
        )
        parser.add_argument(
            '--igreja-id',
            type=int,
            help='ID da igreja que recebera os membros.'
        )
        parser.add_argument(
            '--igreja-slug',
            help='Slug da igreja que recebera os membros.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Valida a importacao sem gravar no banco.'
        )
        parser.add_argument(
            '--atualizar',
            action='store_true',
            help='Atualiza membros existentes encontrados pelo mesmo nome na igreja.'
        )

    def handle(self, *args, **options):
        arquivo = Path(options['arquivo'])

        if not arquivo.exists():
            raise CommandError(f'Arquivo nao encontrado: {arquivo}')

        igreja = self.get_igreja(options)
        linhas = read_xlsx(arquivo)

        if not linhas:
            raise CommandError('A planilha esta vazia.')

        cabecalho = normalize_headers(linhas[0])
        membros = linhas[1:]
        criados = 0
        atualizados = 0
        ignorados = 0

        self.stdout.write(f'Igreja: {igreja.nome}')
        self.stdout.write(f'Arquivo: {arquivo}')
        self.stdout.write(f'Registros encontrados: {len(membros)}')

        with transaction.atomic():
            for numero_linha, linha in enumerate(membros, start=2):
                dados = row_to_member_data(cabecalho, linha)

                if not dados['nome']:
                    ignorados += 1
                    self.stdout.write(
                        self.style.WARNING(f'Linha {numero_linha}: sem nome, ignorada.')
                    )
                    continue

                membro = None

                if options['atualizar']:
                    membro = Membro.objects.filter(
                        igreja=igreja,
                        nome__iexact=dados['nome']
                    ).first()

                if membro:
                    for campo, valor in dados.items():
                        setattr(membro, campo, valor)

                    membro.igreja = igreja
                    membro.save()
                    atualizados += 1
                else:
                    Membro.objects.create(
                        igreja=igreja,
                        **dados
                    )
                    criados += 1

            if options['dry_run']:
                transaction.set_rollback(True)

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run concluido. Nada foi gravado.'))

        self.stdout.write(self.style.SUCCESS(f'Criados: {criados}'))
        self.stdout.write(self.style.SUCCESS(f'Atualizados: {atualizados}'))
        self.stdout.write(self.style.WARNING(f'Ignorados: {ignorados}'))

    def get_igreja(self, options):
        igreja_id = options.get('igreja_id')
        igreja_slug = options.get('igreja_slug')

        if not igreja_id and not igreja_slug:
            raise CommandError('Informe --igreja-id ou --igreja-slug.')

        if igreja_id and igreja_slug:
            raise CommandError('Informe apenas --igreja-id ou --igreja-slug.')

        try:
            if igreja_id:
                return Igreja.objects.get(id=igreja_id)

            return Igreja.objects.get(slug=igreja_slug)
        except Igreja.DoesNotExist as exc:
            raise CommandError('Igreja nao encontrada.') from exc


def read_xlsx(path):
    with ZipFile(path) as archive:
        shared_strings = read_shared_strings(archive)
        sheet_path = get_first_sheet_path(archive)
        root = ET.fromstring(archive.read(sheet_path))
        rows = []

        for row in root.findall('.//a:sheetData/a:row', XML_NS):
            values = []

            for cell in row.findall('a:c', XML_NS):
                index = cell_ref_to_index(cell.attrib.get('r', ''))

                while len(values) <= index:
                    values.append('')

                values[index] = read_cell_value(cell, shared_strings)

            rows.append(values)

        return rows


def read_shared_strings(archive):
    if 'xl/sharedStrings.xml' not in archive.namelist():
        return []

    root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
    values = []

    for item in root.findall('a:si', XML_NS):
        texts = [
            text.text or ''
            for text in item.findall('.//a:t', XML_NS)
        ]
        values.append(''.join(texts))

    return values


def get_first_sheet_path(archive):
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    first_sheet = workbook.find('.//a:sheets/a:sheet', XML_NS)

    if first_sheet is None:
        raise CommandError('Nenhuma aba encontrada na planilha.')

    relation_id = first_sheet.attrib[
        '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    ]

    for relation in rels:
        if relation.attrib.get('Id') == relation_id:
            target = relation.attrib['Target']
            return f'xl/{target}'

    raise CommandError('Nao foi possivel localizar a primeira aba da planilha.')


def read_cell_value(cell, shared_strings):
    value_node = cell.find('a:v', XML_NS)

    if value_node is None:
        return ''

    value = value_node.text or ''

    if cell.attrib.get('t') == 's':
        return shared_strings[int(value)]

    return value


def cell_ref_to_index(cell_ref):
    letters = ''.join(char for char in cell_ref if char.isalpha())
    index = 0

    for char in letters:
        index = index * 26 + ord(char.upper()) - 64

    return index - 1


def normalize_headers(headers):
    return [
        normalize_text(header)
        for header in headers
    ]


def row_to_member_data(headers, row):
    values = {
        header: get_value(row, index)
        for index, header in enumerate(headers)
    }

    return {
        'nome': clean_text(values.get('nome')),
        'email': clean_text(values.get('e-mail')) or None,
        'telefone': clean_phone(values.get('fone com zap')) or None,
        'data_nascimento': excel_date(values.get('dt.nascimento')),
        'endereco': clean_text(values.get('endereco')) or None,
        'bairro': clean_text(values.get('bairro')) or None,
        'cidade': clean_text(values.get('cidade')) or None,
        'status': map_status(values.get('situacao')),
        'cargo': None,
        'batizado': map_bool(values.get('batizado')),
        'data_batismo': None,
    }


def get_value(row, index):
    if index >= len(row):
        return ''

    return row[index]


def clean_text(value):
    if value is None:
        return ''

    return str(value).strip()


def normalize_text(value):
    replacements = {
        'á': 'a',
        'à': 'a',
        'ã': 'a',
        'â': 'a',
        'é': 'e',
        'ê': 'e',
        'í': 'i',
        'ó': 'o',
        'ô': 'o',
        'õ': 'o',
        'ú': 'u',
        'ç': 'c',
    }
    text = clean_text(value).lower()

    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    return text


def clean_phone(value):
    value = clean_text(value)

    if not value:
        return ''

    if value.endswith('.0'):
        value = value[:-2]

    return ''.join(char for char in value if char.isdigit())


def excel_date(value):
    value = clean_text(value)

    if not value:
        return None

    try:
        serial = Decimal(value)
        return EXCEL_EPOCH + timedelta(days=int(serial))
    except Exception:
        pass

    for date_format in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


def map_bool(value):
    value = normalize_text(value)

    return value in (
        'sim',
        's',
        'yes',
        'true',
        '1',
    )


def map_status(value):
    value = normalize_text(value)

    if value == 'visitante':
        return 'VISITANTE'

    if value == 'congregado':
        return 'CONGREGADO'

    if value == 'inativo':
        return 'INATIVO'

    return 'MEMBRO'
