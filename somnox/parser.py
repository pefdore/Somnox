"""Extraction structurée des paramètres de polygraphie à partir du texte brut.

Conçu pour les rapports Nox A1/T3 (noxT3s) exportés en français, avec
tolérance pour les variantes de libellés et les rapports génériques
(IAH/AHI, virgule décimale, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import PolygraphData

_NUM = r"(\d{1,3}[.,]?\d{0,2})"


def _f(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _search(pattern: str, text: str, flags: int = re.IGNORECASE | re.MULTILINE) -> float | None:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    return _f(m.group(1))


def _first(patterns: list[str], text: str) -> float | None:
    for p in patterns:
        v = _search(p, text)
        if v is not None:
            return v
    return None


def _patient(text: str) -> str:
    m = re.search(r"Patient\s*:\s*(.+)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"Nom\s*:\s*(.+)", text, re.IGNORECASE)
    if not m:
        return ""
    return m.group(1).strip()[:80]


def _date_examen(text: str) -> str:
    m = re.search(r"(?:Date d(?:'|e |u )?(?:examen|enregistrement)\s*:\s*|Enregistré le\s*:?)(.{0,30})", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d{2}[/.-]\d{2}[/.-]\d{4})", text)
    return m.group(1).strip() if m else ""


def parse_text(text: str, source: str = "", methode: str = "") -> PolygraphData:
    data = PolygraphData(texte_brut=text, source=source, methode_extraction=methode)
    data.patient = _patient(text)
    data.date_examen = _date_examen(text)

    data.iah = _first(
        [
            rf"\bIAH\b[^0-9\n]*{_NUM}",
            rf"Index\s+d['’]apnées[\s–-]*hypopnées[^0-9\n]*{_NUM}",
            rf"\bAHI\b[^0-9\n]*{_NUM}",
        ],
        text,
    )
    data.index_apnees = _first([rf"\bIA\b[^0-9\n]*{_NUM}", rf"Index\s+d['’]apnées\b[^0-9\n]*{_NUM}", rf"\bAI\b[^0-9\n]*{_NUM}"], text)
    data.index_hypopnees = _first([rf"\bIH\b[^0-9\n]*{_NUM}", rf"Index\s+d['’]hypopnées\b[^0-9\n]*{_NUM}", rf"\bHI\b[^0-9\n]*{_NUM}"], text)
    data.index_desat = _first(
        [
            rf"Index\s+de\s+désaturation[^0-9\n]*{_NUM}",
            rf"\bODI\b[^0-9\n]*{_NUM}",
            rf"IDI\b[^0-9\n]*{_NUM}",
        ],
        text,
    )
    data.iah_rem = _first([rf"IAH\s*(?:en\s*)?REM[^0-9\n]*{_NUM}", rf"AHI\s*REM[^0-9\n]*{_NUM}"], text)
    data.iah_dorsal = _first([rf"IAH\s+décubitus\s*dorsal[^0-9\n]*{_NUM}", rf"IAH\s*dorsal[^0-9\n]*{_NUM}", rf"AHI\s*supine[^0-9\n]*{_NUM}"], text)
    data.iah_latéral = _first([rf"IAH\s*(?:décubitus\s*)?latéral[^0-9\n]*{_NUM}", rf"AHI\s*lat(?:eral|éral)?[^0-9\n]*{_NUM}"], text)

    m = re.search(r"SpO2?\s*moyenne[^0-9\n]*(\d{2,3}[.,]?\d{0,1})", text, re.IGNORECASE)
    data.spo2_moyenne = _f(m.group(1)) if m else None
    m = re.search(r"SpO2?\s*(?:mini(?:male|male)?|minimale|la plus basse)[^0-9\n]*(\d{2,3})", text, re.IGNORECASE)
    data.spo2_minimale = _f(m.group(1)) if m else None
    data.t90 = _first(
        [
            rf"Temps\s+passé\s+sous\s*90\s*%[^0-9\n]*{_NUM}",
            rf"\bT90\b[^0-9\n]*{_NUM}",
            rf"SpO2?\s*<\s*90\s*%[^0-9\n]*{_NUM}",
        ],
        text,
    )

    data.index_micro_eveils = _first(
        [
            rf"Index\s+de\s+micro[\s-]*éveils?[^0-9\n]*{_NUM}",
            rf"Index\s+micro[\s-]*éveils?[^0-9\n]*{_NUM}",
            rf"\bArousal\s*index\b[^0-9\n]*{_NUM}",
        ],
        text,
    )
    data.index_pvt = _first([rf"Index\s+de\s+pressions\s+ventilatoires\s+transitoires[^0-9\n]*{_NUM}", rf"\bRERA\b[^0-9\n]*{_NUM}"], text)
    data.index_plm = _first(
        [
            rf"Index\s+(?:PLM| mouvements\s+périodiques\s+des\s+jambes)[^0-9\n]*{_NUM}",
            rf"\bPLMS?I?\b[^0-9\n]*{_NUM}",
        ],
        text,
    )
    data.index_plm_eveils = _first([rf"Index\s+PLM\s+avec\s+(?:micro[\s-]*)?éveils?[^0-9\n]*{_NUM}"], text)

    data.temps_enregistrement_min = _first(
        [rf"Durée\s+d['’]enregistrement[^0-9\n]*(?:\(min\))?[^0-9\n]*{_NUM}", rf"Temps\s+d['’]enregistrement[^0-9\n]*{_NUM}"], text
    )
    data.temps_analyse_min = _first(
        [rf"Durée\s+d['’]analyse[^0-9\n]*(?:\(min\))?[^0-9\n]*{_NUM}", rf"Temps\s+d['’]analyse[^0-9\n]*{_NUM}", rf"Analyse\s*\(min\)[^0-9\n]*{_NUM}"], text
    )
    data.temps_sommeil_estime_min = _first(
        [rf"Temps\s+de\s+sommeil\s+estimé[^0-9\n]*{_NUM}", rf"Sommeil\s+estimé[^0-9\n]*{_NUM}"], text
    )

    data.ronflement_pct = _first([rf"Ronflement[^0-9\n]*{_NUM}\s*%", rf"Snoring[^0-9\n]*{_NUM}\s*%"], text)
    data.position_dorsale_pct = _first([rf"Décubitus\s+dorsal[^0-9\n]*{_NUM}\s*%", rf"\bSupine\b[^0-9\n]*{_NUM}\s*%", rf"Position\s+dorsale[^0-9\n]*{_NUM}\s*%"], text)

    m = re.search(r"Fréquence\s+cardiaque\s+moyenne[^0-9\n]*(\d{2,3})", text, re.IGNORECASE)
    data.fc_moyenne = int(_f(m.group(1))) if m else None
    m = re.search(r"Fréquence\s+cardiaque\s+maximale[^0-9\n]*(\d{2,3})", text, re.IGNORECASE)
    data.fc_maximale = int(_f(m.group(1))) if m else None

    m = re.search(r"IMC[^0-9\n]*(\d{2}[.,]\d)", text, re.IGNORECASE)
    data.imc = _f(m.group(1)) if m else None
    m = re.search(r"Poids[^0-9\n]*(\d{2,3}[.,]?\d{0,1})", text, re.IGNORECASE)
    data.poids = _f(m.group(1)) if m else None
    m = re.search(r"Taille[^0-9\n]*(\d{3})", text, re.IGNORECASE)
    data.taille = _f(m.group(1)) if m else None
    m = re.search(r"Epworth[^0-9\n]*(\d{1,2})", text, re.IGNORECASE)
    data.epworth = int(_f(m.group(1))) if m else None

    for key, pat in {
        "apnées obstructives": r"Apnées\s+obstructives[^0-9\n]*(\d{1,4})",
        "apnées centrales": r"Apnées\s+centrales[^0-9\n]*(\d{1,4})",
        "apnées mixtes": r"Apnées\s+mixtes[^0-9\n]*(\d{1,4})",
        "hypopnées": r"Hypopnées[^0-9\n]*(\d{1,4})",
        "désaturations": r"Désaturations[^0-9\n]*(\d{1,4})",
    }.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            data.evenements_respiratoires[key] = int(m.group(1))
    return data


def parse_pdf(pdf_path: str | Path) -> PolygraphData:
    from .ingest import extract_text

    pdf_path = Path(pdf_path)
    text, methode = extract_text(pdf_path)
    return parse_text(text, source=str(pdf_path), methode=methode)
