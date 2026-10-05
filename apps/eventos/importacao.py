import re
import unicodedata
import zipfile
from datetime import datetime, time, timedelta
from xml.etree import ElementTree as ET

NS = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = {'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REQUIRED_COLUMNS = ('LOCAL', 'EVENTO', 'HORA', 'DATA', 'DIRIGENTE', 'PREGADOR')


def _normalize(value):
    text = str(value or '').strip().upper()
    return ''.join(char for char in unicodedata.normalize('NFKD', text) if not unicodedata.combining(char))


def _column_index(ref):
    letters = ''.join(char for char in ref if char.isalpha())
    result = 0
    for char in letters:
        result = result * 26 + ord(char.upper()) - 64
    return result - 1


def _read_workbook(uploaded_file):
    with zipfile.ZipFile(uploaded_file) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared = [''.join(node.text or '' for node in item.iter('{%s}t' % NS['a'])) for item in root.findall('a:si', NS)]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheet = workbook.find('a:sheets/a:sheet', NS)
        if sheet is None:
            raise ValueError('A planilha não possui nenhuma aba.')
        relation_id = sheet.attrib.get('{%s}id' % REL_NS['r'])
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next((item.attrib.get('Target') for item in rels if item.attrib.get('Id') == relation_id), None)
        if not target:
            raise ValueError('Não foi possível localizar a aba da planilha.')
        target = target.lstrip('/')
        if not target.startswith('xl/'):
            target = 'xl/' + target
        worksheet = ET.fromstring(archive.read(target))
        rows = []
        for row in worksheet.findall('.//a:sheetData/a:row', NS):
            values = {}
            for cell in row.findall('a:c', NS):
                value = cell.find('a:v', NS)
                inline = cell.find('a:is/a:t', NS)
                if inline is not None:
                    text = inline.text or ''
                elif value is None:
                    text = ''
                elif cell.attrib.get('t') == 's':
                    text = shared[int(value.text)]
                else:
                    text = value.text or ''
                values[_column_index(cell.attrib.get('r', ''))] = text
            rows.append([values.get(index, '') for index in range(max(values.keys(), default=-1) + 1)])
        return rows


def _excel_date(value):
    if not value:
        return None
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    for pattern in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _excel_times(value):
    text = str(value or '').strip()
    if not text:
        return None, None
    matches = re.findall(r'(?<!\d)(\d{1,2}):(\d{2})(?::\d{2})?', text)
    if matches:
        parsed = [time(int(hour), int(minute)) for hour, minute, *_ in matches]
        return parsed[0], parsed[1] if len(parsed) > 1 else None
    try:
        seconds = round(float(text) * 24 * 60 * 60)
        return time(seconds // 3600, (seconds % 3600) // 60), None
    except (TypeError, ValueError):
        return None, None


def parse_eventos_xlsx(uploaded_file):
    rows = _read_workbook(uploaded_file)
    if not rows:
        raise ValueError('A planilha está vazia.')
    headers = {_normalize(value): index for index, value in enumerate(rows[0])}
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise ValueError('Colunas obrigatórias ausentes: %s.' % ', '.join(missing))
    parsed, errors = [], []
    for excel_row, source in enumerate(rows[1:], start=2):
        values = {column: (source[index] if index < len(source) else '') for column, index in headers.items()}
        if not any(str(value).strip() for value in values.values()):
            continue
        title = str(values.get('EVENTO', '')).strip()
        event_date = _excel_date(values.get('DATA'))
        start, end = _excel_times(values.get('HORA'))
        if not title:
            errors.append('Linha %d: EVENTO está vazio.' % excel_row)
            continue
        if not event_date:
            errors.append('Linha %d: DATA inválida.' % excel_row)
            continue
        if not start:
            errors.append('Linha %d: HORA inválida.' % excel_row)
            continue
        dirigente = str(values.get('DIRIGENTE', '')).strip()
        pregador = str(values.get('PREGADOR', '')).strip()
        parsed.append({'titulo': title[:150], 'local': str(values.get('LOCAL', '')).strip()[:150], 'data': event_date.isoformat(), 'hora_inicio': start.isoformat(), 'hora_fim': end.isoformat() if end else '', 'descricao': 'Dirigente: %s\nPregador: %s' % (dirigente, pregador)})
    return parsed, errors