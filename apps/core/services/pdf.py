from io import BytesIO

from django.template.loader import render_to_string
from xhtml2pdf import pisa


def render_pdf(template_name: str, context: dict) -> bytes:
    html = render_to_string(template_name, context)
    buf = BytesIO()
    pisa.CreatePDF(html, dest=buf)
    return buf.getvalue()
