import re
import unicodedata


def _clean_text(value, max_length):
    normalized = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    normalized = re.sub(r'[^A-Za-z0-9 ]+', '', normalized).strip().upper()
    return normalized[:max_length] or 'IGREJA'


def _field(field_id, value):
    value = str(value)
    return f'{field_id}{len(value):02d}{value}'


def _crc16(payload):
    crc = 0xFFFF
    for byte in payload.encode('ascii'):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f'{crc:04X}'


def pix_payload(key, merchant_name, city):
    key = (key or '').strip()
    if not key:
        return ''
    merchant_account = _field('00', 'BR.GOV.BCB.PIX') + _field('01', key)
    additional_data = _field('05', '***')
    payload = ''.join([
        _field('00', '01'),
        _field('26', merchant_account),
        _field('52', '0000'),
        _field('53', '986'),
        _field('58', 'BR'),
        _field('59', _clean_text(merchant_name, 25)),
        _field('60', _clean_text(city, 15)),
        _field('62', additional_data),
    ])
    return payload + '6304' + _crc16(payload + '6304')
