"""Modèle de données d'une polygraphie ventilatoire (noxT3s et générique)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PolygraphData:
    """Champs extraits d'un enregistrement de polygraphie ventilatoire."""

    patient: str = ""
    age: str = ""
    date_naissance: str = ""
    date_examen: str = ""
    indications: str = ""
    poids: Optional[float] = None
    taille: Optional[float] = None
    imc: Optional[float] = None
    epworth: Optional[int] = None

    temps_enregistrement_min: Optional[float] = None
    temps_analyse_min: Optional[float] = None
    temps_sommeil_estime_min: Optional[float] = None

    iah: Optional[float] = None
    index_apnees: Optional[float] = None
    index_hypopnees: Optional[float] = None
    index_desat: Optional[float] = None
    iah_dorsal: Optional[float] = None
    iah_latéral: Optional[float] = None
    iah_rem: Optional[float] = None
    iahc: Optional[float] = None
    iaho: Optional[float] = None

    spo2_moyenne: Optional[float] = None
    spo2_minimale: Optional[float] = None
    spo2_min_rem: Optional[float] = None
    t90: Optional[float] = None
    t90_min: Optional[float] = None
    charge_hypoxique: Optional[float] = None

    index_micro_eveils: Optional[float] = None
    index_pvt: Optional[float] = None
    index_plm: Optional[float] = None
    index_plm_eveils: Optional[float] = None
    activations_autonomiques: Optional[float] = None
    temps_eveil_min: Optional[float] = None

    ronflement_pct: Optional[float] = None
    ronflement_index: Optional[float] = None
    ronflement_dbc_moy: Optional[float] = None
    ronflement_dbc_max: Optional[float] = None
    fc_moyenne: Optional[float] = None
    fc_maximale: Optional[float] = None

    position_dorsale_pct: Optional[float] = None
    pichot: Optional[int] = None
    boss: Optional[int] = None
    evenements_respiratoires: dict = field(default_factory=dict)
    texte_brut: str = ""
    source: str = ""
    methode_extraction: str = ""

    def to_dict(self) -> dict:
        return {
            k: getattr(self, k)
            for k in self.__dataclass_fields__
            if k not in ("evenements_respiratoires", "texte_brut")
        } | {"evenements_respiratoires": dict(self.evenements_respiratoires)}


@dataclass
class ClinicalContext:
    """Contexte clinique saisi par le praticien (absent du PDF noxturnal)."""

    somnolence: bool = False
    fatigue: bool = False
    nycturie: bool = False
    cephees_matinales: bool = False
    ronflements_constates: bool = False
    comorbidites: list[str] = field(default_factory=list)
    refus_ppc: bool = False
    controle_oam: bool = False
    epworth: Optional[int] = None
    boss: Optional[int] = None
    pichot: Optional[int] = None
    notes: str = ""

    @property
    def somnolence_positive(self) -> bool:
        return self.somnolence or (self.epworth is not None and self.epworth >= 10)

    @property
    def risque_accidentogene(self) -> bool:
        return self.boss is not None and self.boss >= 3


SYMPTOMES_UI = {
    "somnolence": "Somnolence diurne",
    "fatigue": "Fatigue",
    "nycturie": "Nycturie",
    "cephees_matinales": "Céphalées matinales",
    "ronflements_constates": "Ronflements constatés",
}

COMORBIDITES_UI = (
    "HTA",
    "diabète",
    "syndrome métabolique",
    "insuffisance cardiaque",
    "ACFA",
    "AVC/AIT",
    "coronaropathie",
)


def default_context(data: PolygraphData) -> ClinicalContext:
    """Pré-remplit le contexte clinique depuis les données extraites du PDF."""
    ctx = ClinicalContext(epworth=data.epworth, pichot=data.pichot, boss=data.boss)
    if data.epworth is not None and data.epworth >= 10:
        ctx.somnolence = True
    if data.indications and ("oam" in data.indications.lower()):
        ctx.controle_oam = True
    return ctx
