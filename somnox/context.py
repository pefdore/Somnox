"""Contexte clinique extrait de la zone « Indications » du rapport Noxturnal.

Deux formats :
- primo PGV : symptômes et comorbidités en « oui/non » + scores
  (Epworth x/24, Pichot x/32, BOSS x/8) ;
- contrôle post-OAM (ou post-PPC) : valeurs pré-traitement puis post-traitement
  (« postOAM : Pichot 18 - Epworth 6 - BOSS 0 ») — on retient les valeurs post.
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

    if ctx.epworth is None:
        ctx.epworth = data.epworth
    if ctx.pichot is None:
        ctx.pichot = data.pichot
    if ctx.boss is None:
        ctx.boss = data.boss
    if ctx.epworth is not None and ctx.epworth >= 10:
        ctx.somnolence = True
    return ctx
