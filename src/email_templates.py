"""
Email template rendering for Wagoner Management Corp.

Produces branded HTML emails matching the B3 mockup: dark header with gold "WMC"
branding, gold summary strip, store-grouped cards with color-coded attendance,
and a dark footer. All templates use table-based layout with inline CSS for
maximum email client compatibility.
"""

import html
from dataclasses import dataclass, field
from datetime import date, datetime


# -- Dataclasses --


@dataclass
class AttendanceRecord:
    store: str
    name: str
    shift_time: datetime
    clock_in_time: datetime | None
    minutes_diff: float | None
    record_type: str  # "early", "late", or "no show on shift"


@dataclass
class MissingPunch:
    store: str
    name: str
    start_time: datetime


@dataclass
class MealPeriodViolation:
    store: str
    name: str
    day: date
    shift_start: datetime


@dataclass
class StoreCard:
    store_id: str
    store_name: str
    drawer_opens: int
    attendance: list[AttendanceRecord] = field(default_factory=list)
    missing_punches: list[MissingPunch] = field(default_factory=list)
    mpvs: list[MealPeriodViolation] = field(default_factory=list)


@dataclass
class DailyJournalData:
    report_date: date
    store_cards: list[StoreCard]
    total_no_shows: int
    total_late: int
    total_early: int
    total_mpvs: int
    total_drawer_opens: int


# -- Font stacks --

_SERIF = "Georgia,serif"
_SANS = "Arial,Helvetica,sans-serif"
_SYSTEM = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif"

# -- Colors --

_DARK = "#2C2416"
_GOLD = "#D4A853"
_MUTED = "#8B7355"
_CREAM_BG = "#f4f1ec"
_CARD_HEADER_BG = "#F5F0E8"
_CARD_HEADER_BORDER = "#E8E2D6"
_ROW_BORDER = "#f5f3ef"

_RED_BG = "#FEF2F2"
_RED_TEXT = "#91200e"
_RED_LABEL = "#7a2020"
_RED_BORDER = "#FECACA"

_YELLOW_BG = "#FFFBEB"
_YELLOW_TEXT = "#92400E"

_GREEN_BG = "#F0FDF4"
_GREEN_TEXT = "#166534"

_MPV_RED = "#C8102E"
_DIVIDER_GOLD = "#b8892e"


# -- Private render helpers --


def _esc(text: str) -> str:
    return html.escape(str(text))


def _fmt_date_short(dt: datetime | date) -> str:
    """Format as 'Feb 15'."""
    return dt.strftime("%b ") + str(dt.day)


def _fmt_time(dt: datetime) -> str:
    """Format as '10:10 AM' (no leading zero on hour)."""
    hour = dt.hour % 12 or 12
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p")
    return f"{hour}:{minute} {ampm}"


def _wrap_document(body: str) -> str:
    return (
        '<!DOCTYPE html>\n<html>\n<head><meta charset="utf-8"></head>\n'
        f'<body style="margin:0;padding:0;background:{_CREAM_BG};">\n'
        f'<table width="100%" cellpadding="0" cellspacing="0" style="background:{_CREAM_BG};padding:20px 0;">\n'
        '<tr><td align="center">\n'
        '<table width="600" cellpadding="0" cellspacing="0">\n'
        f'{body}'
        '</table>\n'
        '</td></tr>\n'
        '</table>\n'
        '</body>\n</html>'
    )


def _render_header(title: str, subtitle: str) -> str:
    return (
        f'<tr><td style="background:{_DARK};border-radius:8px 8px 0 0;padding:20px 24px;">\n'
        '  <table width="100%" cellpadding="0" cellspacing="0">\n'
        '  <tr>\n'
        '    <td>\n'
        f'      <div style="font-family:{_SERIF};font-size:24px;font-weight:800;color:{_GOLD};letter-spacing:2px;">WMC</div>\n'
        f'      <div style="font-family:{_SANS};font-size:10px;font-weight:500;color:{_MUTED};text-transform:uppercase;letter-spacing:2px;margin-top:2px;">Wagoner Management Corp.</div>\n'
        '    </td>\n'
        '    <td align="right" valign="bottom">\n'
        f'      <div style="font-family:{_SANS};font-size:14px;font-weight:600;color:#F5F0E8;">{_esc(title)}</div>\n'
        f'      <div style="font-family:{_SANS};font-size:12px;font-weight:400;color:{_MUTED};margin-top:2px;">{_esc(subtitle)}</div>\n'
        '    </td>\n'
        '  </tr>\n'
        '  </table>\n'
        '</td></tr>\n'
    )


def _render_footer() -> str:
    return (
        '<tr><td style="padding:4px 0 0;">\n'
        f'  <table width="100%" cellpadding="0" cellspacing="0" style="background:{_DARK};border-radius:0 0 8px 8px;overflow:hidden;">\n'
        f'    <tr><td style="padding:14px 24px;">\n'
        f'      <span style="font-family:{_SANS};font-size:11px;font-weight:400;color:{_MUTED};">Josiah &middot; Wagoner Management Corp.</span>\n'
        '    </td></tr>\n'
        '  </table>\n'
        '</td></tr>\n'
    )


def _render_summary_metric(label: str, value: int, is_alert: bool = False) -> str:
    label_color = _RED_LABEL if is_alert else _DARK
    label_opacity = "" if is_alert else "opacity:0.7;"
    value_color = _RED_TEXT if is_alert else _DARK
    return (
        f'<td align="center" width="20%" style="padding:0 4px;">\n'
        f'  <div style="font-family:{_SANS};font-size:10px;font-weight:600;color:{label_color};text-transform:uppercase;letter-spacing:0.5px;{label_opacity}">{_esc(label)}</div>\n'
        f'  <div style="font-family:{_SERIF};font-size:22px;font-weight:800;color:{value_color};line-height:1.2;">{value}</div>\n'
        '</td>\n'
    )


def _render_summary_divider() -> str:
    return f'<td width="1" style="background:{_DIVIDER_GOLD};font-size:0;">&nbsp;</td>\n'


def _render_summary_strip(data: DailyJournalData) -> str:
    metrics = [
        ("Drawer Opens", data.total_drawer_opens, False),
        ("No Shows", data.total_no_shows, True),
        ("Late", data.total_late, False),
        ("Early", data.total_early, False),
        ("Meal Violations", data.total_mpvs, True),
    ]
    cells = []
    for i, (label, value, is_alert) in enumerate(metrics):
        if i > 0:
            cells.append(_render_summary_divider())
        cells.append(_render_summary_metric(label, value, is_alert))

    return (
        f'<tr><td style="background:{_GOLD};padding:14px 24px;">\n'
        '  <table width="100%" cellpadding="0" cellspacing="0">\n'
        '  <tr>\n'
        f'    {"".join(cells)}'
        '  </tr>\n'
        '  </table>\n'
        '</td></tr>\n'
    )


def _render_attendance_row(record: AttendanceRecord) -> str:
    if record.record_type == "no show on shift":
        bg = _RED_BG
        name_color = _RED_TEXT
        name_weight = "font-weight:600;"
        detail_color = _RED_TEXT
        border_color = _RED_BORDER
        detail_text = f"{_fmt_date_short(record.shift_time)}, {_fmt_time(record.shift_time)} shift"
        badge_html = (
            f'<td align="right" style="font-family:{_SANS};font-size:10px;font-weight:600;'
            f'color:{_RED_TEXT};padding:5px 8px;border-bottom:1px solid {_RED_BORDER};'
            f'text-transform:uppercase;letter-spacing:0.5px;">no show</td>\n'
        )
    elif record.record_type == "late":
        bg = _YELLOW_BG
        name_color = _DARK
        name_weight = ""
        detail_color = _MUTED
        border_color = _ROW_BORDER
        minutes = abs(int(record.minutes_diff)) if record.minutes_diff is not None else 0
        detail_text = f"{_fmt_date_short(record.clock_in_time)}, in {_fmt_time(record.clock_in_time)}" if record.clock_in_time else ""
        badge_html = (
            f'<td align="right" style="font-family:{_SANS};font-size:11px;font-weight:600;'
            f'color:{_YELLOW_TEXT};padding:5px 8px;border-bottom:1px solid {_ROW_BORDER};">'
            f'{minutes} min late</td>\n'
        )
    else:  # early
        bg = _GREEN_BG
        name_color = _DARK
        name_weight = ""
        detail_color = _MUTED
        border_color = _ROW_BORDER
        minutes = abs(int(record.minutes_diff)) if record.minutes_diff is not None else 0
        detail_text = f"{_fmt_date_short(record.clock_in_time)}, in {_fmt_time(record.clock_in_time)}" if record.clock_in_time else ""
        badge_html = (
            f'<td align="right" style="font-family:{_SANS};font-size:11px;font-weight:600;'
            f'color:{_GREEN_TEXT};padding:5px 8px;border-bottom:1px solid {_ROW_BORDER};">'
            f'{minutes} min early</td>\n'
        )

    return (
        f'<tr style="background:{bg};">\n'
        f'  <td style="font-family:{_SYSTEM};font-size:12px;color:{name_color};{name_weight}'
        f'padding:5px 8px;border-bottom:1px solid {border_color};">{_esc(record.name)}</td>\n'
        f'  <td style="font-family:{_SYSTEM};font-size:12px;color:{detail_color};'
        f'padding:5px 8px;border-bottom:1px solid {border_color};">{_esc(detail_text)}</td>\n'
        f'  {badge_html}'
        '</tr>\n'
    )


def _render_section_header(label: str, color: str = _MUTED) -> str:
    return (
        f'<tr><td style="padding:12px 20px 4px;">\n'
        f'  <div style="font-family:{_SANS};font-size:11px;font-weight:600;color:{color};'
        f'text-transform:uppercase;letter-spacing:0.5px;">{_esc(label)}</div>\n'
        '</td></tr>\n'
    )


def _render_missing_punch_row(mp: MissingPunch) -> str:
    return (
        '<tr>\n'
        f'  <td style="font-family:{_SYSTEM};font-size:12px;color:{_DARK};padding:2px 0;">'
        f'{_esc(mp.name)}</td>\n'
        f'  <td align="right" style="font-family:{_SYSTEM};font-size:12px;color:{_MUTED};padding:2px 0;">'
        f'{_esc(_fmt_date_short(mp.start_time))}, clocked in {_esc(_fmt_time(mp.start_time))}</td>\n'
        '</tr>\n'
    )


def _render_mpv_row(mpv: MealPeriodViolation) -> str:
    return (
        '<tr>\n'
        f'  <td style="font-family:{_SYSTEM};font-size:12px;color:{_MPV_RED};padding:2px 0;">'
        f'{_esc(mpv.name)}</td>\n'
        f'  <td style="font-family:{_SYSTEM};font-size:12px;color:{_MPV_RED};padding:2px 0;">'
        f'{_esc(_fmt_date_short(mpv.day))}</td>\n'
        f'  <td align="right" style="font-family:{_SYSTEM};font-size:12px;color:{_MPV_RED};padding:2px 0;">'
        f'Shift {_esc(_fmt_time(mpv.shift_start))}</td>\n'
        '</tr>\n'
    )


def _render_store_card(card: StoreCard) -> str:
    drawer_label = f"{card.drawer_opens} drawer open{'s' if card.drawer_opens != 1 else ''}"

    parts = []

    # Store header
    parts.append(
        f'<tr><td style="padding:12px 20px;background:{_CARD_HEADER_BG};border-bottom:1px solid {_CARD_HEADER_BORDER};">\n'
        '  <table width="100%" cellpadding="0" cellspacing="0">\n'
        '  <tr>\n'
        '    <td>\n'
        f'      <span style="font-family:{_SANS};font-size:15px;font-weight:700;color:{_DARK};">{_esc(card.store_id)}</span>\n'
        f'      <span style="font-family:{_SANS};font-size:14px;font-weight:500;color:{_MUTED};"> {_esc(card.store_name)}</span>\n'
        '    </td>\n'
        '    <td align="right">\n'
        f'      <span style="font-family:{_SANS};font-size:11px;font-weight:600;color:{_MUTED};">{_esc(drawer_label)}</span>\n'
        '    </td>\n'
        '  </tr>\n'
        '  </table>\n'
        '</td></tr>\n'
    )

    # Attendance section
    if card.attendance:
        parts.append(_render_section_header("Attendance"))
        rows = "".join(_render_attendance_row(r) for r in card.attendance)
        parts.append(
            '<tr><td style="padding:4px 20px 12px;">\n'
            '  <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">\n'
            f'    {rows}'
            '  </table>\n'
            '</td></tr>\n'
        )

    # Missing punches section
    if card.missing_punches:
        parts.append(_render_section_header("Missing Punches"))
        rows = "".join(_render_missing_punch_row(mp) for mp in card.missing_punches)
        parts.append(
            '<tr><td style="padding:2px 20px 14px;">\n'
            '  <table width="100%" cellpadding="0" cellspacing="0">\n'
            f'    {rows}'
            '  </table>\n'
            '</td></tr>\n'
        )

    # Meal period violations section
    if card.mpvs:
        label = "Meal Period Violation" if len(card.mpvs) == 1 else "Meal Period Violations"
        parts.append(_render_section_header(label, color=_MPV_RED))
        rows = "".join(_render_mpv_row(mpv) for mpv in card.mpvs)
        parts.append(
            '<tr><td style="padding:2px 20px 14px;">\n'
            '  <table width="100%" cellpadding="0" cellspacing="0">\n'
            f'    {rows}'
            '  </table>\n'
            '</td></tr>\n'
        )

    inner = "".join(parts)
    return (
        '<tr><td style="padding:0 0 12px;">\n'
        '  <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;'
        'border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);">\n'
        f'    {inner}'
        '  </table>\n'
        '</td></tr>\n'
    )


def _render_alert_card(body_html: str) -> str:
    return (
        '<tr><td style="padding:12px 0;">\n'
        '  <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;'
        'border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);">\n'
        f'    <tr><td style="padding:20px 24px;font-family:{_SYSTEM};font-size:14px;'
        f'color:{_DARK};line-height:1.6;">\n'
        f'      {body_html}\n'
        '    </td></tr>\n'
        '  </table>\n'
        '</td></tr>\n'
    )


# -- Public render functions --


def render_daily_journal(data: DailyJournalData) -> str:
    """Render the Daily Journal Report as a complete HTML document."""
    subtitle = data.report_date.strftime("%A, %B ") + str(data.report_date.day) + data.report_date.strftime(", %Y")

    parts = []
    parts.append(_render_header("Daily Journal Report", subtitle))
    parts.append(_render_summary_strip(data))

    # Spacer between summary and cards
    parts.append('<tr><td style="height:12px;font-size:0;line-height:0;">&nbsp;</td></tr>\n')

    for card in data.store_cards:
        parts.append(_render_store_card(card))

    parts.append(_render_footer())

    return _wrap_document("".join(parts))


def render_alert_email(title: str, alert_date: date, body_html: str) -> str:
    """Render a branded alert email (missing deposit, high pay-in, etc.)."""
    subtitle = alert_date.strftime("%A, %B ") + str(alert_date.day) + alert_date.strftime(", %Y")

    parts = []
    parts.append(_render_header(title, subtitle))
    parts.append(_render_alert_card(body_html))
    parts.append(_render_footer())

    return _wrap_document("".join(parts))


def render_tips_email(subject: str, report_date: date) -> str:
    """Render a branded wrapper for the tip spreadsheet attachment email."""
    subtitle = report_date.strftime("%A, %B ") + str(report_date.day) + report_date.strftime(", %Y")

    body_html = (
        f'<div style="font-family:{_SYSTEM};font-size:14px;color:{_DARK};line-height:1.6;">'
        'Attached is the tip spreadsheet for your review.</div>'
    )

    parts = []
    parts.append(_render_header(subject, subtitle))
    parts.append(_render_alert_card(body_html))
    parts.append(_render_footer())

    return _wrap_document("".join(parts))
