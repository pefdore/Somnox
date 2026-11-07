"""Modèle de données d'une polygraphie ventilatoire (noxT3s et générique)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PolygraphData:
    """Champs extraits d'un enregistrement de polygraphie ventilatoire."""

    patient: str = ""
    date_naissance: str = ""
    date_examen: str = ""
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

    spo2_moyenne: Optional[float] = None
    spo2_minimale: Optional[float] = None
    t90: Optional[float] = None

    index_micro_eveils: Optional[float] = None
    index_pvt: Optional[float] = None
    index_plm: Optional[float] = None
    index_plm_eveils: Optional[float] = None

    ronflement_pct: Optional[float] = None
    fc_moyenne: Optional[int] = None
    fc_maximale: Optional[int] = None

    position_dorsale_pct: Optional[float] = None
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
