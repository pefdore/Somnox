"""Moteur d'analyse experte selon les recommandations françaises.

Références principales :
- SFARS/SFRMS : cotation et interprétation de la polygraphie ventilatoire
  (seuils IAH 5/15/30 par heure, limites d'analyse sans EEG).
- HAS, guide-parcours « Syndrome d'apnées obstructives du sommeil » (2023).
- Conditions de prise en charge PPC / OAM : IAH ≥ 15/h AVEC comorbidités,
  ou IAH ≥ 30/h (± comorbidités) pour la PPC ; OAM si IAH ≥ 15/h SANS
  comorbidités (ou refus de la PPC).
- Arrêté révisé du 28 mars 2022 : SAHOS + somnolence et conduite automobile.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import ClinicalContext, PolygraphData, default_context

SEUIL_LEGERS = 5.0
SEUIL_MODERES = 15.0
SEUIL_SEVERES = 30.0

COMORBIDITES_CONNUES = (
    "HTA",
    "diabète",
    "syndrome métabolique",
    "insuffisance cardiaque",
    "ACFA",
    "AVC/AIT",
    "coronaropathie",
)

ARRETE_SOMNOLENCE = (
    "Le patient est notifié de l'arrêté révisé du 28 mars 2022, qui met le SAHOS, "
    "dans un contexte de somnolence, sur la liste des incapacités physiques "
    "incompatibles avec l'obtention ou le maintien du permis de conduire, de la "
    "nécessité de se signaler à la commission départementale des permis de conduire "
    "ou à un médecin agréé, de sa propre initiative, pour valider son permis de "
    "conduire. La reprise de la conduite n'est possible qu'après une réévaluation "
    "clinique au minimum après un mois de traitement efficace et, selon l'arrêté de "
    "mars 2022, après la réalisation d'un Test de Maintien d'Éveil (TME) pour le "
    "groupe léger (tous les 3 ans) et le groupe lourd (tous les ans)."
)

ARRETE_RAPPEL = (
    "Le patient n'a pas de somnolence (Epworth à {epworth}) et le risque "
    "accidentogène est jugé faible (BOSS à {boss}), ceci étant je rappelle de façon "
    "systématique que l'arrêté révisé du 28 mars 2022 met le SAHOS, lorsqu'il est "
    "couplé à une somnolence, sur la liste des incapacités physiques incompatibles "
    "avec l'obtention ou le maintien du permis de conduire, de la nécessité de se "
    "signaler à la commission départementale des permis de conduire ou à un médecin "
    "agréé, de sa propre initiative, pour valider son permis de conduire. La reprise "
    "de la conduite n'est possible qu'après une réévaluation clinique au minimum "
    "après un mois de traitement efficace et, selon l'arrêté de mars 2022, après la "
    "réalisation d'un Test de Maintien d'Éveil (TME) pour le groupe léger (tous les "
    "3 ans) et le groupe lourd (tous les ans)."
)


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
    proposition_therapeutique: str = ""
    mesures_associees: list[str] = field(default_factory=list)
    suivi: list[str] = field(default_factory=list)
    rappel_arrete: str = ""
    vigilance: list[dict] = field(default_factory=list)


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


def _proposition(data: PolygraphData, ctx: ClinicalContext) -> str:
    iah = data.iah
    if iah is None:
        return "IAH non disponible : pas de proposition thérapeutique possible avant contrôle du document."
    comorb = bool(ctx.comorbidites)
    if iah >= SEUIL_SEVERES:
        return (
            "Indication au remboursement de la PPC : IAH ≥ 30/h (prise en charge due "
            "avec ou sans comorbidités)."
        )
    if iah >= SEUIL_MODERES:
        if ctx.refus_ppc:
            return (
                "Indication au remboursement d'une OAM : IAH entre 15 et 30/h, le "
                "patient refusant la PPC."
            )
        if comorb:
            return (
                "Indication au remboursement de la PPC : IAH entre 15 et 30/h associé à "
                f"des comorbidités ({', '.join(ctx.comorbidites)})."
            )
        return (
            "Indication au remboursement d'une OAM : IAH entre 15 et 30/h sans "
            "comorbidité (la PPC n'est pas prise en charge dans cette configuration)."
        )
    if iah >= SEUIL_LEGERS:
        return (
            "Pas d'indication de remboursement d'une PPC ni d'une OAM (IAH < 15/h) : "
            "mesures hygiéno-diététiques, contrôle clinique et polygraphique à "
            "reconsidérer si aggravation symptomatique."
        )
    return "Pas d'indication de PPC ni d'OAM (IAH < 5/h)."


def _mesures_associees(data: PolygraphData, ctx: ClinicalContext) -> list[str]:
    mesures = []
    if (
        data.iah_dorsal is not None
        and data.iah_latéral is not None
        and data.iah_latéral > 0
        and data.iah_dorsal / data.iah_latéral >= 2
    ):
        mesures.append(
            "Caractère positionnel net : proposer un dispositif anti-dorsal."
        )
    if data.imc is not None and data.imc >= 25:
        mesures.append(
            f"Perte de poids {'impérative' if data.imc >= 30 else 'souhaitable'} "
            f"(IMC {data.imc:g}) : régime hypocalorique + activité physique "
            "(équipe mobile diététique / Activité Physique Adaptée du CH La Guerche "
            "de Bretagne). Une perte de 5 % du poids correspond généralement à une "
            "diminution d'environ 30 % de l'IAH."
        )
    mesures.append(
        "Éviter alcool et sédatifs le soir, qui majorent le risque d'apnées."
    )
    return mesures


def _suivi(data: PolygraphData, ctx: ClinicalContext, proposition: str) -> list[str]:
    suivi = []
    if "OAM" in proposition:
        suivi.append("Contrôle sous OAM à 4 mois (efficacité, tolérance, calage dentaire).")
    if "PPC" in proposition:
        suivi.append("Consultation à 4 mois si mise en place de la PPC (observance, effets résiduels).")
    if ctx.somnolence_positive and (data.iah or 0) < SEUIL_MODERES:
        suivi.append(
            "Polysomnographie si somnolence sévère non expliquée par la polygraphie."
        )
    if (data.iah or 0) < SEUIL_MODERES:
        suivi.append(
            "Pas de rendez-vous systématique mais reste à la disposition du patient, "
            "en particulier en cas d'aggravation des symptômes (nycturie, somnolence, "
            "asthénie marquée, ronflements sévères, céphalées matinales)."
        )
    return suivi


def _rappel_arrete(data: PolygraphData, ctx: ClinicalContext, sah_os: bool) -> str:
    if not sah_os:
        return ""
    if ctx.somnolence_positive or ctx.risque_accidentogene:
        return ARRETE_SOMNOLENCE
    if ctx.epworth is not None and ctx.epworth < 10 and ctx.boss is not None and ctx.boss < 3:
        return ARRETE_RAPPEL.format(epworth=ctx.epworth, boss=ctx.boss)
    return ""


def _vigilance(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> list[dict]:
    items = []
    if ctx.boss is None:
        items.append({"horizon": "immédiat", "texte": "Score de BOSS non renseigné : risque accidentogène non évalué — à compléter avant l'arrêté de conduite."})
    if not ctx.comorbidites:
        items.append({"horizon": "immédiat", "texte": "Comorbidités non renseignées : leur présence conditionne le remboursement de la PPC (IAH 15-30/h). Vérifier HTA, diabète, syndrome métabolique, ACFA, AVC/AIT, coronaropathie."})
    if ctx.epworth is None and data.epworth is None:
        items.append({"horizon": "immédiat", "texte": "Epworth non disponible : somnolence diurne non documentée."})
    centrales = data.evenements_respiratoires.get("apnées centrales")
    total = sum(data.evenements_respiratoires.values())
    if centrales is not None and total > 0 and centrales / total >= 0.5 and (data.iah or 0) >= 5:
        items.append({"horizon": "immédiat", "texte": "Prédominance d'événements centraux : envisager une polysomnographie et rechercher une insuffisance cardiaque avant toute PPC (risque d'apnées sous PPC)."})
    if data.index_plm is not None and data.index_plm >= 15:
        items.append({"horizon": "immédiat", "texte": "Index PLM ≥ 15/h : corréler à un syndrome des jambes sans repos ; ferritinémie à discuter."})
    if ctx.nycturie:
        items.append({"horizon": "à terme", "texte": "Nycturie déclarée : rechercher un retentissement vésical/prostatique et réévaluer sous traitement."})
    if data.imc is not None and data.imc >= 30:
        items.append({"horizon": "à terme", "texte": "Obésité : suivi pondéral structuré ; le contrôle du poids conditionne l'évolution de l'IAH."})
    if (data.iah or 0) >= 5:
        items.append({"horizon": "à terme", "texte": "Évaluation cardiovasculaire : risque accru d'ACFA et d'AVC ; dépistage HTA et troubles du métabolisme glucidique."})
    if res.fiabilite.startswith("Enregistrement insuffisant"):
        items.append({"horizon": "immédiat", "texte": "Enregistrement < 4 h : polygraphie non concluante, à répéter (ou polysomnographie) avant conclusion définitive."})
    return items


def analyse(data: PolygraphData, ctx: ClinicalContext | None = None) -> AnalysisResult:
    ctx = ctx or default_context(data)
    res = AnalysisResult()
    res.fiabilite, res.donnees_manquantes = _fiabilite(data)
    iah = data.iah

    if iah is None:
        res.severite = "Non interprétable"
        res.conclusion = (
            "IAH non extractible du document. Vérifier l'import (PDF natif ou OCR) "
            "avant toute interprétation."
        )
        res.recommandations.append("Contrôler manuellement le document source ou refaire une saisie assistée.")
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
            "symptomatologie évocatrice (somnolence diurne, ronflements, apnées "
            "constatées, comorbidités) — HAS 2023."
        )
        res.interpretation.append(
            "En l'absence d'EEG, la polygraphie sous-estime l'IAH par rapport à la "
            "polysomnographie (fragmentation non mesurée) : un résultat limite ne "
            "permet pas d'exclure le diagnostic (SFARS/SFRMS)."
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
            "Ratio dorsal/latéral ≥ 2 : composante positionnelle significative."
        )

    # Alertes
    if data.spo2_minimale is not None and data.spo2_minimale < 80:
        res.alertes.append(Alerte("critique", "Désaturation profonde", f"SpO2 minimale à {data.spo2_minimale:.0f} % (< 80 %) : risque d'hypoxémie sévère."))
    if data.t90 is not None and data.t90 >= 15:
        res.alertes.append(Alerte("critique", "Hypoxémie prolongée", f"Temps passé sous 90 % : {data.t90:.1f} % — retentissement cardiovasculaire possible."))
    elif data.t90 is not None and data.t90 >= 5:
        res.alertes.append(Alerte("attention", "Hypoxémie", f"Temps passé sous 90 % : {data.t90:.1f} %."))
    if data.fc_maximale is not None and data.fc_maximale >= 120:
        res.alertes.append(Alerte("attention", "Tachycardie nocturne", f"FC maximale nocturne à {data.fc_maximale} bpm : rechercher un retentissement cardiaque."))
    if ctx.somnolence_positive:
        res.alertes.append(Alerte("attention", "Somnolence diurne", "Somnolence diurne évocatrice (Epworth ≥ 10 ou plainte) : retentissement diurne significatif."))
    if data.index_plm is not None and data.index_plm >= 15:
        res.alertes.append(Alerte("attention", "Mouvements périodiques des jambes", f"Index PLM à {data.index_plm:.1f}/h (≥ 15/h) : à corréler à la plainte."))

    # Thérapeutique, mesures, suivi, arrêté
    res.proposition_therapeutique = _proposition(data, ctx)
    res.mesures_associees = _mesures_associees(data, ctx)
    res.suivi = _suivi(data, ctx, res.proposition_therapeutique)
    res.rappel_arrete = _rappel_arrete(data, ctx, iah >= SEUIL_LEGERS)
    res.vigilance = _vigilance(data, ctx, res)
    return res
