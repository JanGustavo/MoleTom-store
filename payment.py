"""
payment.py — Geração de QR Code PIX estático para contribuições MoleTom.

Dependência:
    pip install qrcode[pil]

Como usar:
    from payment import gerar_qr_pix
    img_b64 = gerar_qr_pix("2.00")   # retorna data URL PNG
"""

import base64
import io

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — troque pela sua chave PIX real
# ---------------------------------------------------------------------------
PIX_KEY       = "Jeeh2200@gmail.com"   # ← edite aqui
PIX_NAME      = "Janderson Gustavo"                           # nome do recebedor (máx 25 chars)
PIX_CITY      = "Bayeux"                          # cidade (máx 15 chars)
# ---------------------------------------------------------------------------

VALORES_SUGERIDOS = [
    {"label": "☕ Café", "valor": "0.50"},
    {"label": "🍕 Apoio",  "valor": "1.00"},
    {"label": "🚀 Top",    "valor": "2.00"},
]


# ---------------------------------------------------------------------------
# Geração do payload PIX (EMV / BR Code) — padrão Banco Central do Brasil
# ---------------------------------------------------------------------------

def _crc16(payload: str) -> str:
    """CRC-16/CCITT-FALSE conforme especificação do Banco Central."""
    data = payload.encode("utf-8")
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, "04X")


def _field(id_: str, value: str) -> str:
    return f"{id_}{len(value):02d}{value}"


def _build_pix_payload(chave: str, nome: str, cidade: str, valor: str, txid: str = "***") -> str:
    # Merchant Account Information (ID 26)
    gui  = _field("00", "br.gov.bcb.pix")
    key  = _field("01", chave)
    mai  = _field("26", gui + key)

    # Valor
    valor_fmt = f"{float(valor):.2f}"
    transaction_amount = _field("54", valor_fmt)

    # Merchant name / city
    merchant_name = _field("59", nome[:25])
    merchant_city = _field("60", cidade[:15])

    # Additional data (txid)
    txid_field    = _field("05", txid)
    add_data      = _field("62", txid_field)

    payload = (
        _field("00", "01")          # Payload Format Indicator
        + _field("01", "12")        # Point of Initiation Method (12 = reutilizável)
        + mai
        + _field("52", "0000")      # Merchant Category Code
        + _field("53", "986")       # Transaction Currency (BRL)
        + transaction_amount
        + _field("58", "BR")        # Country Code
        + merchant_name
        + merchant_city
        + add_data
        + "6304"                    # CRC placeholder
    )
    return payload + _crc16(payload)


def gerar_qr_pix(valor: str) -> str:
    """
    Gera o QR Code PIX para o valor informado.
    Retorna uma data URL base64 PNG pronta para usar em <img src="...">.
    """
    import qrcode

    payload = _build_pix_payload(PIX_KEY, PIX_NAME, PIX_CITY, valor)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def get_valores_sugeridos():
    return VALORES_SUGERIDOS