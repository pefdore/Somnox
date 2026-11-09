"""Contexte clinique extrait de la zone « Indications » du rapport Noxturnal.

Formats pris en charge :
- primo PGV : symptômes et comorbidités en « oui/non » + scores
  (Epworth x/24, Pichot x/32, BOSS x/8) ;
- contrôle post-OAM historique : « pré-OAM : ... / postOAM : ... » ;
- suivi OAM à 4 mois (format structuré) :
  « Suivi OAM (4 mois) : Observance : X j/sem, X h/nuit | Tolérance : ... |
   Réglage actuel : X mm (+X mm depuis la pose) | Clinique : ... |
   Scores : Pre-OAM -> Post-OAM : Epworth : X -> X/24 | ... |
   Métrique Initiale : IAH : X/h | IDO : X/h | T90 : X% | SatMin : X% |
   Décision : Efficacité clinique [...] -> Indication PGV de contrôle sous OAM : ... »
"""

from __future__ import annotations

import re

from .models import ClinicalContext, PolygraphData

SYMPTOMES_OUI_NON = {
    "somnolence diurne": "somnolence",
    "ronflements s[ée]v[èe]res": "ronflements_constates",
    "c[ée]phal[ée]es matinales": "cephees_matinales",
    "fatigue diurne": "fatigue",
    "nycturie": "nycturie",
    "sensation d['’][ée]touffement": "sensation_etouffement",
    "somnolence en situation active": "somnolence",
}

COMORBIDITES_OUI_NON = {
    "hta r[ée]sistante": "HTA",
    "acfa r[ée]cidivante": "ACFA",
    "ic symptomatique": "insuffisance cardiaque",
    "maladie coronaire [àa] haut risque": "coronaropathie",
    "atcd avc": "AVC/AIT",
    "bpco s[ée]v[èe]re": "BPCO",
    "asthme mal contr[ôo]l[ée]e?": "asthme",
    "diab[èe]te": "diabète",
}


def _detect_type(indications: str) -> str:
    low = indications.lower()
    if "oam" in low:
        return "controle_oam"
    if "ppc" in low:
        return "controle_ppc"
    return "primo"


def _flag(pattern: str, text: str) -> bool:
    m = re.search(rf"{pattern}\s*:\s*(oui|non)", text, re.IGNORECASE)
    return bool(m and m.group(1).lower() == "oui")


def _num(pattern: str, text: str):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else None


def _parse_suivi_oam(indications: str, ctx: ClinicalContext, data: PolygraphData) -> None:
    """Format structuré « Suivi OAM (4 mois) »."""
    m = re.search(r"Observance\s*:\s*(\d{1,2})\s*j(?:ours)?/s(?:em|emaine)?\s*,\s*(\d{1,2}[.,]?\d{0,1})\s*h(?:eures)?/n(?:uit)?", indications, re.IGNORECASE)
    if m:
        ctx.observance_jours_sem = int(m.group(1))
        ctx.observance_heures_nuit = float(m.group(2).replace(",", "."))

    m = re.search(r"Tol[ée]rance\s*:\s*([^|]{3,60})", indications, re.IGNORECASE)
    if m:
        ctx.tolerance_oam = m.group(1).strip().strip(".,;")

    m = re.search(r"R[ée]glage actuel\s*:\s*(\d{1,2}[.,]?\d{0,1})\s*mm\s*\(\s*\+\s*(\d{1,2}[.,]?\d{0,1})\s*mm", indications, re.IGNORECASE)
    if m:
        ctx.reglage_oam_mm = float(m.group(1).replace(",", "."))
        ctx.reglage_augmentation_mm = float(m.group(2).replace(",", "."))

    # Clinique (modalités enrichies : doute / parfois / X fois)
    m = re.search(r"Ronflements s[ée]v[èe]res\s*:\s*\[?(non|doute|oui)", indications, re.IGNORECASE)
    if m:
        val = m.group(1).lower()
        ctx.ronflements_constates = val == "oui"
        ctx.ronflements_doute = val == "doute"
    m = re.search(r"Fatigue diurne\s*:\s*\[?(non|parfois|oui)", indications, re.IGNORECASE)
    if m:
        val = m.group(1).lower()
        ctx.fatigue = val == "oui"
        ctx.fatigue_parfois = val == "parfois"
    m = re.search(r"Nycturie\s*:\s*\[?(\d{1,2})\s*fois", indications, re.IGNORECASE)
    if m:
        ctx.nycturie_fois = int(m.group(1))
        ctx.nycturie = ctx.nycturie_fois > 0

    # Scores pré -> post
    m = re.search(r"Epworth\s*:\s*(\d{1,2})\s*->\s*(\d{1,2})\s*/\s*24", indications, re.IGNORECASE)
    if m:
        ctx.epworth_pre = int(m.group(1))
        ctx.epworth = int(m.group(2))
    m = re.search(r"Pichot\s*:\s*(\d{1,2})\s*->\s*(\d{1,2})\s*/\s*32", indications, re.IGNORECASE)
    if m:
        ctx.pichot_pre = int(m.group(1))
        ctx.pichot = int(m.group(2))
    m = re.search(r"Boss\s*:\s*(\d{1,2})\s*->\s*(\d{1,2})\s*/\s*8", indications, re.IGNORECASE)
    if m:
        ctx.boss_pre = int(m.group(1))
        ctx.boss = int(m.group(2))

    # Métrique initiale
    m = re.search(r"M[ée]trique Initiale\s*:.*?IAH\s*:\s*(\d{1,3}[.,]?\d*)\s*/h", indications, re.IGNORECASE)
    if m:
        data.iah_pre_traitement = float(m.group(1).replace(",", "."))
    m = re.search(r"M[ée]trique Initiale\s*:.*?IDO\s*:\s*(\d{1,3}[.,]?\d*)\s*/h", indications, re.IGNORECASE)
    if m:
        data.odi_pre_traitement = float(m.group(1).replace(",", "."))
    m = re.search(r"M[ée]trique Initiale\s*:.*?T90\s*:\s*(\d{1,3}[.,]?\d*)\s*%", indications, re.IGNORECASE)
    if m:
        data.t90_pre_traitement = float(m.group(1).replace(",", "."))
    m = re.search(r"M[ée]trique Initiale\s*:.*?SatMin\s*:\s*(\d{2,3})\s*%?", indications, re.IGNORECASE)
    if m:
        data.spo2_min_pre_traitement = float(m.group(1))

    # Décision
    m = re.search(r"Efficacit[ée] clinique\s*\[?(compl[èe]te|partielle|nulle)", indications, re.IGNORECASE)
    if m:
        ctx.efficacite_clinique = {"complète": "complète", "complete": "complète", "partielle": "partielle", "nulle": "nulle"}[m.group(1).lower()]
    m = re.search(r"Indication PGV de contr[ôo]le sous OAM\s*:?\s*\[?(oui|non)", indications, re.IGNORECASE)
    if m:
        ctx.indication_controle_oam = m.group(1).lower() == "oui"


def build_context(data: PolygraphData) -> ClinicalContext:
    indications = data.indications
    ctx = ClinicalContext(type_examen=_detect_type(indications))

    for pattern, attr in SYMPTOMES_OUI_NON.items():
        if _flag(pattern, indications):
            setattr(ctx, attr, True)

    comorbs = [
        label for pattern, label in COMORBIDITES_OUI_NON.items()
        if _flag(pattern, indications)
    ]
    ctx.comorbidites = comorbs

    m = re.search(r"Ep(?:o|wo)rth\s*:\s*(\d{1,2})\s*/\s*24", indications, re.IGNORECASE)
    if m:
        ctx.epworth = int(m.group(1))
    m = re.search(r"Pichot\s*:\s*(\d{1,2})\s*/\s*32", indications, re.IGNORECASE)
    if m:
        ctx.pichot = int(m.group(1))
    m = re.search(r"Boss\s*:\s*(\d{1,2})\s*/\s*8", indications, re.IGNORECASE)
    if m:
        ctx.boss = int(m.group(1))

    m = re.search(r"Autre cause de somnolence possible identifi[ée]e\s*:\s*(.{0,120})", indications, re.IGNORECASE)
    if m:
        ctx.notes = m.group(1).strip()

    if ctx.type_examen == "controle_oam":
        _parse_suivi_oam(indications, ctx, data)

    if ctx.epworth is None:
        ctx.epworth = data.epworth
    if ctx.pichot is None:
        ctx.pichot = data.pichot
    if ctx.boss is None:
        ctx.boss = data.boss
    if ctx.epworth is not None and ctx.epworth >= 10:
        ctx.somnolence = True
    return ctx
