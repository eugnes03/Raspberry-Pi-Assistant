from io import BytesIO
from assistant.utils.logger import setup_logger

logger = setup_logger()


def generate(data: str) -> BytesIO | None:
    """Generate a QR code for `data` and return it as a PNG BytesIO buffer."""
    try:
        import qrcode
    except ImportError:
        logger.error("qrcode package not installed. Run: pip install 'qrcode[pil]'")
        return None

    try:
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return None
