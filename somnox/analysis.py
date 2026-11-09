"""Moteur expert d'analyse — système de règles déterministe (sans IA).

Encodage des recommandations françaises de prise en charge du SAHOS :
- HAS, guide-parcours « Syndrome d'apnées obstructives du sommeil » (2023) ;
- SFARS/SFRMS : cotation et interprétation de la polygraphie ventilatoire ;
- Conditions de prise en charge PPC / OAM (LPP) ;
- Arrêté révisé du 28 mars 2022 (SAHOS, somnolence et conduite automobile) ;
- Repères consensuels : SOH, apnées centrales, SHVAS, PLM, suivi d'observance.

Organisation : fiabilité → diagnostic/sévérité → phénotypage → retentissement
→ somnolence/conduite → thérapeutique → vigilance/checklist.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import ClinicalContext, PolygraphData, default_context

SEUIL_LEGERS = 5.0
SEUIL_MODERES = 15.0
SEUIL_SEVERES = 30.0

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
    diagnostics_differentiels: list[str] = field(default_factory=list)
    bilan_complementaire: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)


class Gravite:
    AUCUNE = "absente"
    LEGERE = "légère"
    MODEREE = "modérée"
    SEVERE = "sévère"


def _alerte(res, niveau, titre, texte):
    res.alertes.append(Alerte(niveau, titre, texte))


def _vigilance(res, horizon, texte):
    res.vigilance.append({"horizon": horizon, "texte": texte})


# ------------------------------------------------------------------ fiabilité

def _fiabilite(data: PolygraphData, res: AnalysisResult) -> None:
    duree = data.temps_analyse_min or data.temps_enregistrement_min
    if duree is not None and duree < 240:
        res.fiabilite = "Enregistrement insuffisant (< 4 h d'analyse) : résultat non concluant."
    elif duree is not None and data.temps_enregistrement_min and data.temps_analyse_min and data.temps_analyse_min / data.temps_enregistrement_min < 0.5:
        res.fiabilite = (
            f"Proportion analysée faible ({data.temps_analyse_min:g}/{data.temps_enregistrement_min:g} min) : "
            "interprétation prudente."
        )
    elif duree is not None:
        res.fiabilite = "Enregistrement de durée satisfaisante (≥ 4 h d'analyse)."
    else:
        res.fiabilite = "Durée d'analyse non retrouvée : interprétation prudente."
    if data.qualite_enregistrement_pct is not None and data.qualite_enregistrement_pct < 60:
        res.fiabilite += (
            f" Qualité du signal faible ({data.qualite_enregistrement_pct:g} %) : "
            "interprétation prudente, envisager un contrôle si doute."
        )
        _vigilance(res, "immédiat", f"Qualité d'enregistrement à {data.qualite_enregistrement_pct:g} % (< 60 %) : vérifier la validité des signaux (flux nasal, oxymétrie) avant conclusion.")

    if data.temps_analyse_min is None and data.temps_enregistrement_min is None:
        res.donnees_manquantes.append("durée d'enregistrement/analyse")
    if data.spo2_minimale is None:
        res.donnees_manquantes.append("SpO2 minimale")
    if data.index_desat is None:
        res.donnees_manquantes.append("index de désaturation")


# ---------------------------------------------------- diagnostic et sévérité

def _diagnostic(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    iah = data.iah
    if iah is None:
        res.severite = "Non interprétable"
        res.conclusion = "IAH non extractible du document : vérifier l'import avant toute interprétation."
        res.recommandations.append("Contrôler le document source ou refaire une saisie assistée.")
        res.checklist.append("IAH non extractible : valider manuellement les valeurs sur le PDF.")
        return

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

    symptomes = any([ctx.somnolence, ctx.fatigue, ctx.nycturie, ctx.cephees_matinales, ctx.ronflements_constates, ctx.sensation_etouffement])
    if iah >= SEUIL_LEGERS:
        res.interpretation.append(
            "Le diagnostic de SAHOS sur polygraphie exige un IAH ≥ 5/h associé à une "
            "symptomatologie évocatrice (somnolence, ronflements, apnées constatées, "
            "comorbidités) — HAS 2023."
        )
        if not symptomes:
            res.checklist.append(
                "IAH pathologique mais symptomatologie non renseignée : documenter les symptômes "
                "avant d'affirmer le syndrome d'apnées du sommeil."
            )
        res.interpretation.append(
            "En l'absence d'EEG, la polygraphie sous-estime l'IAH par rapport à la "
            "polysomnographie (fragmentation non mesurée) : un résultat limite ne permet "
            "pas d'exclure le diagnostic (SFARS/SFRMS)."
        )
    elif symptomes and ctx.somnolence_positive:
        res.diagnostics_differentiels.append(
            "Somnolence avec IAH normal : envisager un syndrome de haute résistance des "
            "voies aériennes supérieures (SHVAS) — polysomnographie à discuter."
        )

    if data.index_desat is not None and iah >= SEUIL_LEGERS:
        if abs(data.index_desat - iah) > max(10, 0.3 * iah):
            res.interpretation.append(
                f"Discordance IAH/IDO ({iah:g} vs {data.index_desat:g}/h) : vérifier le signal de flux "
                "(fuite nasale, respiration bouche) et la qualité de l'oxymétrie."
            )
            _vigilance(res, "immédiat", "Discordance IAH/IDO marquée : contrôler la validité du flux nasal et de l'oxymétrie avant conclusion.")
        else:
            res.interpretation.append(f"Index de désaturation à {data.index_desat:.1f}/h concordant avec l'IAH.")


# ------------------------------------------------------------------ phénotypage

def _phenotype(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    iah = data.iah or 0.0

    # Prédominance centrale
    centrales = data.evenements_respiratoires.get("apnées centrales", 0)
    tot_apnees = centrales + data.evenements_respiratoires.get("apnées obstructives", 0) + data.evenements_respiratoires.get("apnées mixtes", 0)
    central_majoritaire = (
        (data.iahc is not None and data.iaho is not None and data.iahc > data.iaho)
        or (tot_apnees > 0 and centrales / tot_apnees >= 0.5)
    )
    if central_majoritaire and iah >= SEUIL_LEGERS:
        _alerte(res, "attention", "Prédominance d'apnées centrales",
                "Majorité d'événements centraux : envisager une polysomnographie et rechercher "
                "une insuffisance cardiaque / un trouble central (prudence avant PPC : risque "
                "d'apnées centrales émergentes sous PPC).")
        res.bilan_complementaire.append("Bilan cardiologique si prédominance centrale : ECG/ETT, BNP, recherche d'insuffisance cardiaque ou d'ACFA.")
        res.recommandations.append("Avis spécialisé avant PPC si prédominance centrale confirmée.")
        res.checklist.append(
            "Apnées centrales détectées : lancer l'analyse « respiration de Cheyne-Stokes » dans "
            "Nox Journal (elle n'est PAS automatique) avant de conclure — et vérifier le tracé "
            "sur la fenêtre correspondante."
        )
        if data.cheyne_stokes_min is None:
            res.checklist.append(
                "Durée Cheyne-Stokes non extractible : soit l'analyse n'a pas été lancée, soit le "
                "rapport est antérieur — relancer l'analyse Cheyne-Stokes dans Nox Journal."
            )

    # Stades de sommeil : l'analyse Nox Body Sleep a-t-elle été exécutée ?
    if data.duree_rem_min is None:
        _vigilance(res, "immédiat",
                   "Stades de sommeil non détectés dans le rapport : l'analyse Nox Body Sleep "
                   "(éveil/NREM/REM) n'a probablement pas été exécutée — la lancer pour préciser "
                   "l'IAH REM, la fragmentation et le temps de sommeil avant conclusion.")
    elif data.duree_rem_min < 30:
        _vigilance(res, "immédiat",
                   f"Temps de REM insuffisant ({data.duree_rem_min:g} min < 30 min) : interpréter "
                   "l'IAH REM avec prudence (SAHOS REM possiblement sous-estimé).")

    if data.cheyne_stokes_min is not None and data.cheyne_stokes_min > 0:
        _alerte(res, "critique", "Respiration de Cheyne-Stokes",
                f"Durée Cheyne-Stokes : {data.cheyne_stokes_min:g} min — évoquer une respiration "
                "périodique centrale (insuffisance cardiaque, AVC) : avis cardiologique et PSG.")
        res.bilan_complementaire.append("Cheyne-Stokes : ETT, BNP, avis cardiologique (respiration périodique centrale).")

    # Positionnel
    if (
        data.iah_dorsal is not None
        and data.iah_latéral is not None
        and data.iah_latéral > 0
        and data.iah_dorsal / data.iah_latéral >= 2
    ):
        res.interpretation.append(
            f"Ratio dorsal/non-dorsal ≥ 2 ({data.iah_dorsal:g} vs {data.iah_latéral:g}/h) : "
            "composante positionnelle significative."
        )
        if iah < SEUIL_MODERES and data.iah_latéral < SEUIL_LEGERS:
            res.recommandations.append(
                "SAHOS positionnel pur en latéral : dispositif anti-dorsal efficace attendu en "
                "première intention."
            )

    # REM
    if data.iah_rem is not None and data.iah_rem >= 15 and (data.iah or 0) < 15:
        res.interpretation.append(
            f"IAH en REM à {data.iah_rem:.1f}/h : SAHOS REM à considérer malgré un IAH global peu élevé."
        )
        _vigilance(res, "à terme", "SAHOS REM : surveiller l'aggravation avec l'âge et la prise de poids ; réévaluer si symptômes.")

    # Suspicion d'hypoventilation / SOH
    if (
        data.imc is not None and data.imc >= 30
        and ((data.t90 or 0) >= 5 or (data.spo2_moyenne or 100) < 92)
    ):
        _alerte(res, "attention", "Suspicion de syndrome d'obésité-hypoventilation (SOH)",
                "Obésité avec hypoxémie nocturne : rechercher une hypoventilation alvéolaire "
                "(gaz du sang diurnes, bicarbonates).")
        res.bilan_complementaire.append("Gaz du sang diurnes + bicarbonates : éliminer un syndrome d'obésité-hypoventilation (PPC à mode alvéolaire si confirmé).")

    # PLM
    if data.index_plm is not None and data.index_plm >= 15:
        _alerte(res, "attention", "Mouvements périodiques des jambes",
                f"Index PLM à {data.index_plm:.1f}/h (≥ 15/h) : corréler à la plainte.")
        res.bilan_complementaire.append("Si syndrome des jambes sans repos : ferritinémie (et CRP) à doser.")
        if ctx.fatigue and (data.iah or 0) < SEUIL_LEGERS:
            res.diagnostics_differentiels.append("PLM élevés avec IAH normal : fragmentation par mouvements périodiques — PSG si plainte de sommeil non expliquée.")

    # Fragmentation
    if data.activations_autonomiques is not None and data.activations_autonomiques >= 30:
        res.interpretation.append(
            f"Activations autonomiques très élevées ({data.activations_autonomiques:g}/h) : "
            "fragmentation importante du sommeil."
        )


# ------------------------------------------------ retentissement cardiovasculaire

def _retentissement(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    if data.spo2_minimale is not None and data.spo2_minimale < 80:
        _alerte(res, "critique", "Désaturation profonde", f"SpO2 minimale à {data.spo2_minimale:.0f} % (< 80 %) : hypoxémie sévère.")
    if data.t90 is not None and data.t90 >= 15:
        _alerte(res, "critique", "Hypoxémie prolongée", f"Temps passé sous 90 % : {data.t90:.1f} %.")
    elif data.t90 is not None and data.t90 >= 5:
        _alerte(res, "attention", "Hypoxémie", f"Temps passé sous 90 % : {data.t90:.1f} %.")
    if data.fc_maximale is not None and data.fc_maximale >= 120:
        _alerte(res, "attention", "Tachycardie nocturne", f"FC maximale nocturne à {data.fc_maximale:g} bpm : rechercher un retentissement cardiaque.")
    if data.fc_minimale is not None and data.fc_minimale < 40:
        _alerte(res, "attention", "Bradycardie nocturne", f"FC minimale à {data.fc_minimale:g} bpm : vérifier si bradycardies en rapport avec les apnées (bloc auriculo-ventriculaire à éliminer si récurrentes).")

    if (data.iah or 0) >= SEUIL_LEGERS:
        res.bilan_complementaire.append("Recherche de comorbidités : TA (domicile), HbA1c, bilan lipidique (HTA, diabète, syndrome métabolique).")
        res.bilan_complementaire.append("Évaluation cardiovasculaire : risque accru d'ACFA et d'AVC ; ECG, avis cardiologique si ACFA/IC connues.")
    if "HTA" in ctx.comorbidites and (data.iah or 0) >= SEUIL_LEGERS:
        res.recommandations.append("HTA associée : contrôler la TA sous traitement ; l'efficacité du traitement du SAHOS peut améliorer le contrôle tensionnel.")
    if data.imc is not None and data.imc >= 30:
        _alerte(res, "info", "Obésité", f"IMC à {data.imc:.1f} kg/m² : facteur de risque et cible thérapeutique.")


# --------------------------------------------------- somnolence et conduite

def _somnolence(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    if ctx.somnolence_positive:
        _alerte(res, "attention", "Somnolence diurne", "Somnolence diurne évocatrice (Epworth ≥ 10 ou plainte) : retentissement significatif.")
        if ctx.epworth is not None and ctx.epworth >= 16 and (data.iah or 0) < SEUIL_MODERES:
            res.diagnostics_differentiels.append(
                "Somnolence sévère (Epworth ≥ 16) disproportionnée à l'IAH : éliminer narcolepsie "
                "(PSG + tests itératifs de latence), hypothyroïdie (TSH), syndrome des jambes sans "
                "repos, dette de sommeil, dépression."
            )
            res.bilan_complementaire.append("TSH, ferritinémie ; avis spécialisé sommeil si somnolence sévère non expliquée.")
    if ctx.notes:
        res.interpretation.append(f"Autre cause de somnolence identifiée : {ctx.notes} — à traiter parallèlement.")
    if ctx.nycturie:
        _vigilance(res, "à terme", "Nycturie : rechercher un retentissement vésical/prostatique et réévaluer sous traitement.")

    sah_os = (data.iah or 0) >= SEUIL_LEGERS
    if sah_os:
        if ctx.somnolence_positive or ctx.risque_accidentogene:
            res.rappel_arrete = ARRETE_SOMNOLENCE
        elif ctx.epworth is not None and ctx.epworth < 10 and ctx.boss is not None and ctx.boss < 3:
            res.rappel_arrete = ARRETE_RAPPEL.format(epworth=ctx.epworth, boss=ctx.boss)
    if sah_os and ctx.boss is None:
        res.checklist.append("BOSS non renseigné : risque accidentogène non évalué — compléter avant l'information de conduite.")


# -------------------------------------------------------------- thérapeutique

def _therapeutique(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    iah = data.iah
    if iah is None:
        return
    comorb = bool(ctx.comorbidites)

    if ctx.type_examen == "controle_oam":
        if iah < SEUIL_MODERES:
            res.proposition_therapeutique = (
                f"Contrôle sous OAM à 4 mois : efficacité confirmée (IAH résiduel à {iah:g}/h, "
                "< 15/h). Poursuite de l'OAM."
            )
        elif iah < SEUIL_SEVERES:
            base = (
                f"Contrôle sous OAM à 4 mois : réponse insuffisante (IAH résiduel à {iah:g}/h, "
                "≥ 15/h) — vérifier calage dentaire, observance et avancée mandibulaire ; "
            )
            if comorb:
                base += ("en cas d'échec, bascule vers la PPC (prise en charge possible : "
                         f"IAH ≥ 15/h avec comorbidités : {', '.join(ctx.comorbidites)}).")
            else:
                base += "en cas d'échec, réévaluer les options (PPC non prise en charge sans comorbidité à ce stade)."
            res.proposition_therapeutique = base
        else:
            res.proposition_therapeutique = (
                f"Contrôle sous OAM à 4 mois : échec (IAH résiduel à {iah:g}/h, ≥ 30/h) — "
                "bascule vers la PPC (prise en charge due, IAH ≥ 30/h avec ou sans comorbidités)."
            )
    elif ctx.type_examen == "controle_ppc":
        if iah < SEUIL_MODERES:
            res.proposition_therapeutique = (
                f"Contrôle sous PPC : contrôle favorable (IAH résiduel à {iah:g}/h, < 15/h). "
                "Poursuite du traitement, contrôle de l'observance."
            )
        else:
            res.proposition_therapeutique = (
                f"Contrôle sous PPC : IAH résiduel à {iah:g}/h — vérifier observance, étanchéité du "
                "circuit, masque, pression et position ; envisager une réoptimisation (auto-PPC, "
                "pression fixe majorée) ou un avis spécialisé."
            )
    else:
        if iah >= SEUIL_SEVERES:
            res.proposition_therapeutique = (
                "Indication au remboursement de la PPC : IAH ≥ 30/h (prise en charge due avec ou "
                "sans comorbidités)."
            )
        elif iah >= SEUIL_MODERES:
            if ctx.refus_ppc:
                res.proposition_therapeutique = (
                    "Indication au remboursement d'une OAM : IAH entre 15 et 30/h, le patient "
                    "refusant la PPC."
                )
            elif comorb:
                res.proposition_therapeutique = (
                    "Indication au remboursement de la PPC : IAH entre 15 et 30/h associé à des "
                    f"comorbidités ({', '.join(ctx.comorbidites)})."
                )
            else:
                res.proposition_therapeutique = (
                    "Indication au remboursement d'une OAM : IAH entre 15 et 30/h sans comorbidité "
                    "(la PPC n'est pas prise en charge dans cette configuration)."
                )
        elif iah >= SEUIL_LEGERS:
            res.proposition_therapeutique = (
                "Pas d'indication de remboursement d'une PPC ni d'une OAM (IAH < 15/h) : mesures "
                "hygiéno-diététiques, contrôle clinique et polygraphique à reconsidérer si "
                "aggravation symptomatique."
            )
            if ctx.somnolence_positive:
                res.recommandations.append(
                    "Somnolence avec SAHOS léger : réévaluer par polysomnographie si la symptomatologie persiste."
                )
        else:
            res.proposition_therapeutique = "Pas d'indication de PPC ni d'OAM (IAH < 5/h)."

    # Contre-indications / précautions OAM
    if "OAM" in res.proposition_therapeutique:
        res.checklist.append(
            "Avant OAM : vérifier l'absence de contre-indication dentaire (édentation étendue, "
            "parodontopathie active, troubles de l'ATM) — bilan dentaire à prévoir."
        )

    # Mesures associées
    if (
        data.iah_dorsal is not None and data.iah_latéral is not None
        and data.iah_latéral > 0 and data.iah_dorsal / data.iah_latéral >= 2
    ):
        res.mesures_associees.append("Caractère positionnel net : proposer un dispositif anti-dorsal.")
    if data.imc is not None and data.imc >= 25:
        res.mesures_associees.append(
            f"Perte de poids {'impérative' if data.imc >= 30 else 'souhaitable'} (IMC {data.imc:g}) : "
            "régime hypocalorique + activité physique (équipe mobile diététique / Activité Physique "
            "Adaptée du CH La Guerche de Bretagne). Une perte de 5 % du poids correspond "
            "généralement à une diminution d'environ 30 % de l'IAH."
        )
    res.mesures_associees.append("Éviter alcool et sédatifs le soir, qui majorent le risque d'apnées.")

    # Suivi
    if ctx.type_examen == "controle_oam":
        if "efficacité confirmée" in res.proposition_therapeutique:
            res.suivi.append("OAM efficace : poursuite ; contrôle à 12 mois ou si aggravation symptomatique.")
        else:
            res.suivi.append("Nouveau contrôle polygraphique après optimisation de l'OAM (calage/avancée mandibulaire).")
    elif ctx.type_examen == "controle_ppc":
        res.suivi.append("Contrôle clinique à 4 mois (observance, effets résiduels) ; réoptimisation si IAH résiduel ≥ 15/h.")
    else:
        if "OAM" in res.proposition_therapeutique:
            res.suivi.append("Contrôle sous OAM à 4 mois (efficacité, tolérance, calage dentaire).")
        if "PPC" in res.proposition_therapeutique:
            res.suivi.append("Consultation à 4 mois si mise en place de la PPC (observance ≥ 4 h/nuit sur 70 % des nuits, effets résiduels).")
        if ctx.somnolence_positive and (data.iah or 0) < SEUIL_MODERES:
            res.suivi.append("Polysomnographie si somnolence sévère non expliquée par la polygraphie.")
        if (data.iah or 0) < SEUIL_MODERES:
            res.suivi.append(
                "Pas de rendez-vous systématique mais reste à la disposition du patient, en "
                "particulier en cas d'aggravation des symptômes (nycturie, somnolence, asthénie "
                "marquée, ronflements sévères, céphalées matinales)."
            )


# ------------------------------------------------------------------ vigilance

def _comparaison_traitement(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    """Contrôle sous traitement : comparaison pré/post et cohérence de la démarche."""
    if ctx.type_examen == "primo":
        return
    if data.iah is not None and data.iah_pre_traitement is not None:
        variation = (data.iah - data.iah_pre_traitement) / data.iah_pre_traitement * 100 if data.iah_pre_traitement else 0
        sens = "diminution" if variation < 0 else "augmentation"
        res.interpretation.append(
            f"Comparaison pré/post-traitement : IAH {data.iah_pre_traitement:g} → {data.iah:g}/h "
            f"({sens} de {abs(variation):.0f} %)"
            + (f", IDO {data.odi_pre_traitement:g} → {data.index_desat:g}/h." if data.odi_pre_traitement is not None and data.index_desat is not None else ".")
        )
        if abs(variation) < 25:
            _vigilance(res, "immédiat",
                       f"Variation d'IAH faible sous traitement ({variation:+.0f} %) : vérifier "
                       "l'observance (OAM : avancée mandibulaire suffisante ? PPC : masque/pression ?) "
                       "avant de conclure à l'efficacité.")
    else:
        _vigilance(res, "immédiat",
                   "Valeurs pré-traitement non retrouvées dans les Indications : pour un contrôle, "
                   "documenter l'IAH/IDO de référence pour objectiver l'évolution.")
    res.checklist.append(
        "Contrôle sous traitement : ne pas re-chercher les symptômes initiaux mais évaluer les "
        "symptômes SOUS traitement (Epworth/Pichot/BOSS actuels vs initiaux)."
    )


def _vigilance_globale(data: PolygraphData, ctx: ClinicalContext, res: AnalysisResult) -> None:
    if not ctx.comorbidites:
        _vigilance(res, "immédiat",
                   "Comorbidités non renseignées : leur présence conditionne le remboursement de la "
                   "PPC (IAH 15-30/h). Vérifier HTA, diabète, syndrome métabolique, ACFA, AVC/AIT, "
                   "coronaropathie, IC.")
    if ctx.epworth is None and data.epworth is None:
        _vigilance(res, "immédiat", "Epworth non disponible : somnolence diurne non documentée.")
    if res.fiabilite.startswith("Enregistrement insuffisant"):
        _vigilance(res, "immédiat", "Enregistrement < 4 h : polygraphie non concluante, à répéter (ou polysomnographie) avant conclusion définitive.")
    if (data.iah or 0) >= SEUIL_LEGERS and data.imc is not None and data.imc >= 30:
        _vigilance(res, "à terme", "Obésité : suivi pondéral structuré ; le contrôle du poids conditionne l'évolution de l'IAH.")
    if (data.iah or 0) >= SEUIL_LEGERS:
        _vigilance(res, "à terme",
                   "Évaluation cardiovasculaire : risque accru d'ACFA et d'AVC ; dépistage HTA et "
                   "troubles du métabolisme glucidique.")
    res.checklist.append("Relire les tracés bruts du noxT3s (relecture déjà effectuée) et vérifier la concordance des valeurs saisies.")
    res.checklist.append("Vérifier que le patient a bien reçu l'information sur l'hygiène du sommeil et le suivi prévu.")


def analyse(data: PolygraphData, ctx: ClinicalContext | None = None) -> AnalysisResult:
    ctx = ctx or default_context(data)
    res = AnalysisResult()
    _fiabilite(data, res)
    _diagnostic(data, ctx, res)
    if res.severite != "Non interprétable":
        _phenotype(data, ctx, res)
        _retentissement(data, ctx, res)
    _somnolence(data, ctx, res)
    _therapeutique(data, ctx, res)
    _comparaison_traitement(data, ctx, res)
    _vigilance_globale(data, ctx, res)
    return res
