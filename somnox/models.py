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
    fc_minimale: Optional[float] = None
    t85: Optional[float] = None
    cheyne_stokes_min: Optional[float] = None
    cycles_respiration_limitee_pct: Optional[float] = None
    qualite_enregistrement_pct: Optional[float] = None
    efficacite_sommeil_pct: Optional[float] = None

    position_dorsale_pct: Optional[float] = None
    pichot: Optional[int] = None
    iah_pre_traitement: Optional[float] = None
    odi_pre_traitement: Optional[float] = None
    t90_pre_traitement: Optional[float] = None
    spo2_min_pre_traitement: Optional[float] = None
    duree_rem_min: Optional[float] = None
    duree_nrem_min: Optional[float] = None
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
    type_examen: str = "primo"
    sensation_etouffement: bool = False
    epworth: Optional[int] = None
    boss: Optional[int] = None
    pichot: Optional[int] = None
    epworth_pre: Optional[int] = None
    boss_pre: Optional[int] = None
    pichot_pre: Optional[int] = None
    notes: str = ""
    observance_jours_sem: Optional[int] = None
    observance_heures_nuit: Optional[float] = None
    tolerance_oam: str = ""
    reglage_oam_mm: Optional[float] = None
    reglage_augmentation_mm: Optional[float] = None
    efficacite_clinique: str = ""
    indication_controle_oam: Optional[bool] = None
    ronflements_doute: bool = False
    fatigue_parfois: bool = False
    nycturie_fois: Optional[int] = None

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
    "sensation_etouffement": "Sensation d'étouffement",
}

COMORBIDITES_UI = (
    "HTA",
    "diabète",
    "syndrome métabolique",
    "insuffisance cardiaque",
    "ACFA",
    "AVC/AIT",
    "coronaropathie",
    "BPCO",
    "asthme",
)

TYPE_EXAMEN_LABELS = {
    "primo": "Polygraphie de première intention",
    "controle_oam": "Contrôle sous OAM (4 mois)",
    "controle_ppc": "Contrôle sous PPC",
}


def default_context(data: PolygraphData) -> ClinicalContext:
    """Pré-remplit le contexte clinique depuis les Indications du PDF."""
    from .context import build_context

    return build_context(data)
