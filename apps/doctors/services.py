from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_available_slots(doctor_profile, days=14):
    """
    Returns a list of bookable slots for the next `days` days.
    Slots are split into chunks of consultation_duration_min.
    Each entry: {start: UTC ISO, end: UTC ISO, duration_min: int}
    """
    try:
        doctor_tz = ZoneInfo(doctor_profile.timezone)
    except (ZoneInfoNotFoundError, Exception):
        doctor_tz = ZoneInfo("UTC")

    now_utc = datetime.now(dt_timezone.utc)
    now_local = now_utc.astimezone(doctor_tz)
    today = now_local.date()

    duration_min = doctor_profile.consultation_duration_min or 30
    duration = timedelta(minutes=duration_min)

    slots = list(doctor_profile.slots.filter(is_active=True))

    recurring = {}   # day_of_week -> list of slots
    specific = {}    # date -> list of slots

    for s in slots:
        if s.slot_type == "recurring_weekly" and s.day_of_week is not None:
            recurring.setdefault(s.day_of_week, []).append(s)
        elif s.slot_type == "specific_date" and s.specific_date is not None:
            specific.setdefault(s.specific_date, []).append(s)

    # Subtract already-booked appointments (Phase 6 populates these)
    try:
        from apps.consultations.models import Appointment
        window_end = now_utc + timedelta(days=days)
        booked = list(
            Appointment.objects.filter(
                doctor=doctor_profile,
                status__in=["scheduled", "in_progress"],
                scheduled_start__gte=now_utc,
                scheduled_start__lt=window_end,
            ).values("scheduled_start", "scheduled_end")
        )
    except Exception:
        booked = []

    result = []
    for day_offset in range(days):
        day = today + timedelta(days=day_offset)
        weekday = day.weekday()  # 0=Monday, 6=Sunday

        day_slots = []
        if weekday in recurring:
            day_slots.extend(recurring[weekday])
        if day in specific:
            day_slots.extend(specific[day])

        for slot in day_slots:
            # Localize to doctor's timezone (wall clock time on this specific date)
            slot_start_local = datetime.combine(day, slot.start_time).replace(tzinfo=doctor_tz)
            slot_end_local = datetime.combine(day, slot.end_time).replace(tzinfo=doctor_tz)

            chunk_start = slot_start_local
            while chunk_start + duration <= slot_end_local:
                chunk_end = chunk_start + duration
                chunk_start_utc = chunk_start.astimezone(dt_timezone.utc)
                chunk_end_utc = chunk_end.astimezone(dt_timezone.utc)

                if chunk_end_utc <= now_utc:
                    chunk_start += duration
                    continue

                is_booked = any(
                    b["scheduled_start"] < chunk_end_utc and b["scheduled_end"] > chunk_start_utc
                    for b in booked
                )

                if not is_booked:
                    result.append({
                        "start": chunk_start_utc.isoformat(),
                        "end": chunk_end_utc.isoformat(),
                        "duration_min": duration_min,
                    })

                chunk_start += duration

    return result
