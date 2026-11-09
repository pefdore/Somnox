"""Extraction structurée des paramètres de polygraphie à partir du texte brut.

Calé sur les rapports Noxturnal (noxT3s) : libellé et valeur sur des lignes
séparées, tableaux multi-colonnes (Total / Dorsal / Non-dorsal / REM / NREM),
contexte clinique (Pichot, Epworth, BOSS) dans la zone « Indications ».
Les rapports génériques restent pris en charge en repli.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import PolygraphData

_NUM = r"(\d{1,3}[.,]?\d{0,2})"
_GAP = r"[\s\S]{0,40}?"


def _f(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _search(pattern: str, text: str) -> float | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return _f(m.group(1)) if m else None


def _search_all(pattern: str, text: str) -> list[float]:
    return [_f(m.group(1)) for m in re.finditer(pattern, text, re.IGNORECASE)]


def _first(patterns: list[str], text: str) -> float | None:
    for p in patterns:
        v = _search(p, text)
        if v is not None:
            return v
    return None


def _last(patterns: list[str], text: str) -> float | None:
    for p in patterns:
        vals = [v for v in _search_all(p, text) if v is not None]
        if vals:
            return vals[-1]
    return None


def _patient(text: str) -> str:
    m = re.search(r"Patient\s*:\s*(.+)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"Nom\s*:\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip()[:80] if m else ""


def _date_examen(text: str) -> str:
    m = re.search(r"(?:Date d['’](?:examen|enregistrement)\s*:?)(.{0,30})", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(?:Début et fin de l['’]enregistrement\s*\n?)(.{0,30})", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d{2}[/.-]\d{2}[/.-]\d{4})", text)
    if not m:
        return ""
    line = m.group(1).strip().splitlines()[0]
    return line[:30]


def parse_text(text: str, source: str = "", methode: str = "") -> PolygraphData:
    d = PolygraphData(texte_brut=text, source=source, methode_extraction=methode)
    d.patient = _patient(text)
    d.date_examen = _date_examen(text)

    m = re.search(r"[ÂA]ge\s*:?\s*(\d{1,3})\s*ans", text, re.IGNORECASE)
    d.age = f"{m.group(1)} ans" if m else ""
    m = re.search(r"Indications\s*\n([\s\S]*?)(?=\n\s*(?:Charge hypoxique|Param[èe]tres respiratoires)|\n\s*\n|$)", text, re.IGNORECASE)
    d.indications = " ".join(m.group(1).split()) if m else ""

    d.imc = _first([rf"IMC{_GAP}{_NUM}\s*kg/m", rf"IMC[^0-9\n]*{_NUM}"], text)
    d.epworth = None if (v := _last([r"Ep(?:o|wo)rth\s*:?\s*(\d{1,2})", r"Epworth[^0-9\n]*(\d{1,2})"], text)) is None else int(v)
    d.pichot = None if (v := _last([r"Pichot\s*:?\s*(\d{1,2})"], text)) is None else int(v)
    d.boss = None if (v := _last([r"BOSS\s*:?\s*(\d{1,2})"], text)) is None else int(v)

    d.temps_enregistrement_min = _first(
        [rf"Dur[ée]e d['’]enregistrement{_GAP}{_NUM}\s*min", rf"Dur[ée]e d['’]enregistrement[^0-9\n]*{_NUM}"], text
    )
    d.temps_analyse_min = _first(
        [rf"Dur[ée]e d['’]analyse{_GAP}{_NUM}\s*min", rf"Dur[ée]e d['’]analyse[^0-9\n]*{_NUM}"], text
    )

    # IAH : libellé Noxturnal d'abord, sinon replis génériques
    d.iah = _first(
        [
            rf"Index Apn[ée]es Hypopn[ée]es{_GAP}{_NUM}\s*/h",
            rf"\bIAH\b\s*\([^)]*\){_GAP}{_NUM}\s*/h",
            rf"\bIAH\b[^0-9\n]*{_NUM}",
            rf"\bAHI\b[^0-9\n]*{_NUM}",
        ],
        text,
    )
    d.iaho = _first([rf"\bIAHo\b{_GAP}{_NUM}\s*/h", rf"IAHo\b[^0-9\n]*{_NUM}"], text)
    d.iahc = _first([rf"\bIAHc\b{_GAP}{_NUM}\s*/h", rf"IAHc\b[^0-9\n]*{_NUM}"], text)
    d.index_apnees = _first([rf"Apn[ée]es obstructives{_GAP}{_NUM}\s*/h", rf"\bIA\b[^0-9\n]*{_NUM}"], text)
    d.index_hypopnees = _first([rf"Hypopn[ée]es\s*\(\d+[^)]*\){_GAP}{_NUM}\s*/h", rf"Hypopn[ée]es{_GAP}{_NUM}\s*/h", rf"\bIH\b[^0-9\n]*{_NUM}"], text)

    d.index_desat = _first(
        [
            rf"Index de d[ée]saturation[s]? en oxyg[èe]ne\s*\(IDO\){_GAP}{_NUM}\s*/h",
            rf"Index de d[ée]saturations?\s*\(\d+[^)]*\){_GAP}{_NUM}\s*/h",
            rf"Index de d[ée]saturation[s]?\s*:?[\s\S]{{0,20}}?{_NUM}",
            rf"\bIDO\b[^0-9\n]*{_NUM}\s*/h",
            rf"\bODI\b[^0-9\n]*{_NUM}",
        ],
        text,
    )

    d.iah_dorsal = _first([rf"IAH dorsal{_GAP}{_NUM}\s*/h", rf"IAH\s+décubitus\s*dorsal[^0-9\n]*{_NUM}"], text)
    d.iah_latéral = _first([rf"IAH non-dorsal{_GAP}{_NUM}\s*/h", rf"IAH\s*(?:décubitus\s*)?lat[ée]ral[^0-9\n]*{_NUM}"], text)

    # Ligne tableau : Total / Dorsal / Non-dorsal / REM / NREM
    m = re.search(
        r"Apn[ée]es \+ Hypopn[ée]es \(IAH\)[\s\S]{0,10}?(\d+[.,]?\d*)\s*/h"
        r"[\s\S]{0,10}?(\d+[.,]?\d*)\s*/h[\s\S]{0,10}?(\d+[.,]?\d*)\s*/h"
        r"[\s\S]{0,10}?(\d+[.,]?\d*)\s*/h",
        text, re.IGNORECASE,
    )
    if m:
        d.iah_rem = _f(m.group(4))
    if d.iah_rem is None:
        d.iah_rem = _first([rf"IAH\s*(?:en\s*)?REM[^0-9\n]*{_NUM}", rf"AHI\s*REM[^0-9\n]*{_NUM}"], text)

    d.spo2_moyenne = _first([rf"SpO2?\s*moyenne\s*:?\s*{_NUM}\s*%?", rf"SpO2?\s*moyenne[^0-9\n]*{_NUM}"], text)
    d.spo2_minimale = _first([rf"SpO2?\s*minimale\s*:?\s*{_NUM}\s*%?", rf"SpO2?\s*(?:minimale|la plus basse)[^0-9\n]*{_NUM}"], text)

    m = re.search(r"Dur[ée]e SpO2?\s*<\s*90%?\s*\n?\s*(\d{1,3}[.,]?\d*)\s*%?\s*(?:soit\s*(\d+[.,]?\d*)\s*min)?", text, re.IGNORECASE)
    if m:
        d.t90 = _f(m.group(1))
        d.t90_min = _f(m.group(2))
    if d.t90 is None:
        d.t90 = _first([rf"Temps\s+passé\s+sous\s*90\s*%[^0-9\n]*{_NUM}", rf"\bT90\b[^0-9\n]*{_NUM}"], text)
        d.t90_min = _first([rf"SpO2?\s*<\s*90%?\s*\(\s*(\d+[.,]?\d*)\s*min"], text)
    d.charge_hypoxique = _first([rf"Charge hypoxique{_GAP}{_NUM}\s*%?min", rf"Charge\s+hypoxique[^0-9\n]*{_NUM}"], text)

    d.activations_autonomiques = _first([rf"Activations autonomiques\s*\(\d+[^)]*\){_GAP}{_NUM}\s*/h", rf"Activations? autonomiques?[^0-9\n]*{_NUM}"], text)
    m = re.search(r"Eveil\s*\n\s*(\d{1,3})\s*min", text, re.IGNORECASE)
    d.temps_eveil_min = _f(m.group(1)) if m else None

    d.ronflement_pct = _first([rf"Episodes? de ronflements{_GAP}{_NUM}\s*%", rf"Ronflement[^0-9\n]*{_NUM}\s*%"], text)
    d.ronflement_index = _first([rf"Ronflements uniques\s*\(\d+[^)]*\){_GAP}{_NUM}\s*/h"], text)
    d.ronflement_dbc_moy = _first([rf"Volume audio moyen{_GAP}{_NUM}\s*dBc?", rf"Ronflement[^0-9\n]*moyen[^0-9\n]*{_NUM}\s*dBc?"], text)
    d.ronflement_dbc_max = _first([rf"Volume audio maximal{_GAP}{_NUM}\s*dBc?", rf"Ronflement[^0-9\n]*max(?:imal|imum)?[^0-9\n]*{_NUM}\s*dBc?"], text)

    d.fc_moyenne = _first([rf"Pouls moyen{_GAP}{_NUM}\s*bpm", rf"Fr[ée]quence cardiaque moyenne[^0-9\n]*(\d{2,3}[.,]?\d?)"], text)
    d.fc_maximale = _first([rf"Pouls maximal[^\n]*{_GAP}{_NUM}\s*bpm", rf"Fr[ée]quence cardiaque maximale[^0-9\n]*(\d{2,3})"], text)
    d.fc_minimale = _first([rf"Pouls minimal[^\n]*{_GAP}{_NUM}\s*bpm"], text)
    d.t85 = _first([rf"SpO2?\s*[≤<=]\s*85%?\s*\([^)]*\)\s*\n?\s*{_NUM}\s*%"], text)
    d.cheyne_stokes_min = _first([rf"Dur[ée]e Cheyne-Stokes\s*\n?\s*{_NUM}\s*min"], text)
    m = re.search(rf"Cycles resp limit[ée]s[^\n]*\n\s*\d+\s*\n\s*{_NUM}\s*%", text, re.IGNORECASE)
    d.cycles_respiration_limitee_pct = _f(m.group(1)) if m else None
    d.qualite_enregistrement_pct = _first([rf"Qualit[ée] de l['’]enregistrement\s*\n?\s*{_NUM}\s*%"], text)
    d.efficacite_sommeil_pct = _first([rf"Est\. efficacit[ée] du sommeil\s*\n?\s*{_NUM}\s*%"], text)

    # Stades (présents si analyse Nox Body Sleep exécutée)
    nrem = _search(rf"NREM\s*\n\s*{_NUM}\s*min", text)
    rem = _search(rf"(?<![A-Za-z])REM\s*\n\s*{_NUM}\s*min", text)
    d.duree_nrem_min = nrem
    d.duree_rem_min = rem
    if nrem is not None and rem is not None:
        d.temps_sommeil_estime_min = nrem + rem

    # Valeurs pré-traitement dans les Indications (contrôle OAM/PPC)
    m = re.search(r"pr[ée][\s-]*OAM\s*:[^\n]*?IAH\s*(\d+[.,]?\d*)[^\n]*?IDO\s*(\d+[.,]?\d*)", d.indications, re.IGNORECASE)
    if m:
        d.iah_pre_traitement = _f(m.group(1))
        d.odi_pre_traitement = _f(m.group(2))

    d.position_dorsale_pct = _first([rf"Dorsale{_GAP}\d+[.,]?\d*\s*min{_GAP}{_NUM}\s*%", rf"Décubitus\s*dorsal[^0-9\n]*{_NUM}\s*%"], text)

    d.index_plm = _first([rf"Index\s+(?:PLM| mouvements\s+p[ée]riodiques)[^0-9\n]*{_NUM}", rf"\bPLMS?I?\b[^0-9\n]*{_NUM}"], text)
    d.index_micro_eveils = _first([rf"Index\s+de\s+micro[\s-]*[ée]veils?[^0-9\n]*{_NUM}", rf"Arousal\s*index\b[^0-9\n]*{_NUM}"], text)

    for key, pat in {
        "apnées obstructives": r"Apn[ée]es obstructives\s*\n\s*(\d{1,4})",
        "apnées centrales": r"Apn[ée]es centrales\s*\n\s*(\d{1,4})",
        "apnées mixtes": r"Apn[ée]es mixtes\s*\n\s*(\d{1,4})",
        "hypopnées": r"Hypopn[ée]es\s*\n\s*(\d{1,4})\s+soit",
        "désaturations": r"Nombre de d[ée]saturations\s*\n\s*(\d{1,4})",
    }.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            d.evenements_respiratoires[key] = int(m.group(1))
    return d


def parse_pdf(pdf_path: str | Path) -> PolygraphData:
    from .ingest import extract_text

    pdf_path = Path(pdf_path)
    text, methode = extract_text(pdf_path)
    return parse_text(text, source=str(pdf_path), methode=methode)
