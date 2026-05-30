import base64
import secrets
from datetime import timedelta
from io import BytesIO

import qrcode
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.core.services.pdf import render_pdf

from .models import SurgeryCoupon


def _qr_data_uri(text: str) -> str:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def generate_voucher(booking) -> SurgeryCoupon:
    """Create (or regenerate) SurgeryCoupon and its PDF for a booking."""
    today = timezone.now().date()
    code = SurgeryCoupon.generate_code()
    qr_uri = _qr_data_uri(f"MEDIBRIDGE:{booking.id}:{code}")

    coupon, _ = SurgeryCoupon.objects.get_or_create(
        booking=booking,
        defaults={
            "code": code,
            "valid_from": today,
            "valid_until": today + timedelta(days=365),
        },
    )

    pdf_bytes = render_pdf("pdf/surgery_voucher.html", {
        "booking": booking,
        "coupon": coupon,
        "qr_uri": qr_uri,
        "passport_last4": (booking.travel_info.passport_number[-4:]
                           if hasattr(booking, "travel_info") else "****"),
    })

    filename = f"voucher_{booking.id}_{coupon.code[:8]}.pdf"
    coupon.voucher_pdf.save(filename, ContentFile(pdf_bytes), save=True)
    return coupon


def send_voucher_email(booking, coupon) -> None:
    from apps.notifications.services import send_email_with_attachment
    patient = booking.patient
    pdf_bytes = coupon.voucher_pdf.read()
    send_email_with_attachment(
        to_email=patient.user.email,
        subject=f"Your MediBridge Surgery Voucher — {booking.package.name}",
        template_name="voucher_issued",
        context={"booking": booking, "coupon": coupon, "patient": patient},
        context_type="SurgeryPackageBooking",
        context_id=booking.id,
        attachment_filename=f"MediBridge_Voucher_{booking.id}.pdf",
        attachment_content=pdf_bytes,
        attachment_mimetype="application/pdf",
    )
