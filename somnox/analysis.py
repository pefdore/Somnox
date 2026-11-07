"""Moteur d'analyse experte selon les recommandations françaises.

Références principales :
- SFARS/SFRMS : cotation et interprétation de la polygraphie ventilatoire
  (seuils IAH 5/15/30 par heure, limites d'analyse sans EEG).
- HAS, guide-parcours « Syndrome d'apnées obstructives du sommeil » (2023) :
  démarche diagnostique, critères de gravité, orientation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import PolygraphData

SEUIL_LEGERS = 5.0
SEUIL_MODERES = 15.0
SEUIL_SEVERES = 30.0


@dataclass
class Alerte:
    niveau: str
    titre: str
    texte: str


@dataclass
class AnalysisResult:
    severite: str = "Non interprétable"
    conclusion: str = ""
    interpretation: list[str] = field(default_factory=list)
    alertes: list[Alerte] = field(default_factory=list)
    recommandations: list[str] = field(default_factory=list)
    fiabilite: str = ""
    donnees_manquantes: list[str] = field(default_factory=list)


class Gravite:
    AUCUNE = "absente"
    LEGERE = "légère"
    MODEREE = "modérée"
    SEVERE = "sévère"


def _fiabilite(data: PolygraphData) -> tuple[str, list[str]]:
    manquantes = []
    if data.temps_analyse_min is None and data.temps_enregistrement_min is None:
        manquantes.append("durée d'enregistrement/analyse")
    if data.spo2_minimale is None:
        manquantes.append("SpO2 minimale")
    if data.index_desat is None:
        manquantes.append("index de désaturation")

    duree = data.temps_analyse_min or data.temps_enregistrement_min
    if duree is not None and duree < 240:
        return "Enregistrement insuffisant (< 4 h d'analyse) : résultat non concluant.", manquantes
    if duree is None:
        return "Durée d'analyse non retrouvée : interprétation prudente.", manquantes
    return "Enregistrement de durée satisfaisante (≥ 4 h d'analyse).", manquantes


def analyse(data: PolygraphData) -> AnalysisResult:
    res = AnalysisResult()
    res.fiabilite, res.donnees_manquantes = _fiabilite(data)
    iah = data.iah

    if iah is None:
        res.severite = "Non interprétable"
        res.conclusion = (
            "IAH non extractible du document. Vérifier l'import (PDF natif ou OCR) "
            "avant toute interprétation."
        )
        res.recommandations.append(
            "Contrôler manuellement le document source ou refaire une saisie assistée."
        )
        return res

    if iah < SEUIL_LEGERS:
        res.severite = Gravite.AUCUNE
        res.conclusion = "Pas d'argument polygraphique pour un syndrome d'apnées du sommeil (IAH < 5/h)."
    elif iah < SEUIL_MODERES:
        res.severite = Gravite.LEGERE
        res.conclusion = "Polygraphie en faveur d'un SAHOS léger (IAH entre 5 et 14/h)."
    elif iah < SEUIL_SEVERES:
        res.severite = Gravite.MODEREE
        res.conclusion = "Polygraphie en faveur d'un SAHOS modéré (IAH entre 15 et 29/h)."
    else:
        res.severite = Gravite.SEVERE
        res.conclusion = "Polygraphie en faveur d'un SAHOS sévère (IAH ≥ 30/h)."

    if iah >= SEUIL_LEGERS:
        res.interpretation.append(
            "Le diagnostic de SAHOS sur polygraphie exige un IAH ≥ 5/h associé à une "
            "symptomatologie évocatrice (somnolence diurne, ronflements, apnées constatées, "
            "comorbidités) — HAS 2023."
        )
        res.interpretation.append(
            "En l'absence d'EEC, la polygraphie sous-estime l'IAH par rapport à la "
            "polysomnographie (index d'éveils non mesuré) : un résultat limite ne permet "
            "pas d'exclure le diagnostic (SFARS/SFRMS)."
        )

    if data.index_desat is not None:
        res.interpretation.append(
            f"Index de désaturation à {data.index_desat:.1f}/h"
            + (" concordant avec l'IAH." if abs(data.index_desat - iah) <= 10 else " — discordance à explorer (IAH vs ODI).")
        )

    if data.iah_rem is not None and data.iah_rem >= 15 and iah < 15:
        res.interpretation.append(
            f"IAH en REM à {data.iah_rem:.1f}/h : SAHOS positionnel/REM à considérer malgré un IAH global peu élevé."
        )

    if (
        data.iah_dorsal is not None
        and data.iah_latéral is not None
        and data.iah_latéral > 0
        and data.iah_dorsal / data.iah_latéral >= 2
    ):
        res.interpretation.append(
            "Ratio dorsal/latéral ≥ 2 : composante positionnelle significative, à prendre en "
            "compte dans la stratégie thérapeutique (rééducation posturale en complément)."
        )

    # Alertes
    if data.spo2_minimale is not None and data.spo2_minimale < 80:
        res.alertes.append(
            Alerte("critique", "Désaturation profonde",
                   f"SpO2 minimale à {data.spo2_minimale:.0f} % (< 80 %) : risque d'hypoxémie sévère.")
        )
    if data.t90 is not None and data.t90 >= 15:
        res.alertes.append(
            Alerte("critique", "Hypoxémie prolongée",
                   f"Temps passé sous 90 % : {data.t90:.1f} % — retentissement cardiovasculaire possible.")
        )
    elif data.t90 is not None and data.t90 >= 5:
        res.alertes.append(
            Alerte("attention", "Hypoxémie",
                   f"Temps passé sous 90 % : {data.t90:.1f} %.")
        )
    centrales = data.evenements_respiratoires.get("apnées centrales")
    total = sum(data.evenements_respiratoires.values())
    if centrales is not None and total > 0 and centrales / total >= 0.5 and (iah or 0) >= 5:
        res.alertes.append(
            Alerte("attention", "Prédominance d'apnées centrales",
                   "Majorité d'événements centraux : envisager une polysomnographie et rechercher "
                   "une insuffisance cardiaque / un trouble central (précaution avant PPC).")
        )
    if data.fc_maximale is not None and data.fc_maximale >= 120:
        res.alertes.append(
            Alerte("attention", "Tachycardie nocturne",
                   f"FC maximale nocturne à {data.fc_maximale} bpm : rechercher un retentissement cardiaque.")
        )
    if data.epworth is not None and data.epworth >= 11:
        res.alertes.append(
            Alerte("attention", "Somnolence diurne excessive",
                   f"Score d'Epworth à {data.epworth}/24 (≥ 11) : retentissement diurne significatif, "
                   "risque accidentel (conduite, travail).")
        )
    if data.index_plm is not None and data.index_plm >= 15:
        res.alertes.append(
            Alerte("attention", "Mouvements périodiques des jambes",
                   f"Index PLM à {data.index_plm:.1f}/h (≥ 15/h) : à corréler à la plainte ; "
                   "ferritinémie à discuter si syndrome des jambes sans repos.")
        )
    if data.imc is not None and data.imc >= 30:
        res.alertes.append(
            Alerte("info", "Obésité", f"IMC à {data.imc:.1f} kg/m² : facteur de risque et cible thérapeutique (poids).")
        )

    # Recommandations
    if iah >= SEUIL_SEVERES:
        res.recommandations.append(
            "SAHOS sévère : mise en route d'un traitement par PPC à privilégier, avec "
            "auto-titration et évaluation à 3 mois (observance, score résiduel)."
        )
    elif iah >= SEUIL_LEGERS:
        res.recommandations.append(
            "Discuter le traitement selon la symptomatologie : PPC si somnolence diurne "
            "ou comorbidités, orthèse d'avancée mandibulaire ou réduction pondérale sinon."
        )
    if iah < SEUIL_LEGERS and data.index_micro_eveils is not None and data.index_micro_eveils >= 15:
        res.recommandations.append(
            "Index de micro-éveils élevé malgré un IAH normal : envisager une polysomnographie "
            "à la recherche d'un syndrome de haute résistance des voies aériennes supérieures."
        )
    res.recommandations.append(
        "Information du patient sur l'hygiène du sommeil et le suivi (HAS 2023)."
    )
    return res
