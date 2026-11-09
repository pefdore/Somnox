"""Guide d'interprétation intégré — synthèse des recommandations (SFRMS/SFARS, HAS 2023)."""

_BLUE = "#0B57D0"
_DARK = "#041E49"
_TABLE = (
    "border-collapse:collapse;width:100%;margin:8px 0;font-size:13px;"
)
_TH = (
    f"background:{_BLUE};color:#FFFFFF;padding:7px 10px;text-align:left;border-radius:0;"
)
_TD = "padding:6px 10px;border-bottom:1px solid #DDE3EA;"
_CARD = (
    "background:#F8F9FF;border:1px solid #DDE3EA;border-radius:14px;"
    "padding:12px 16px;margin:10px 0;"
)
_H2 = f"color:{_BLUE};font-size:17px;margin:20px 0 6px 0;font-weight:800;"
_LI = "margin:4px 0;"

GUIDE_HTML = f"""
<h2 style='{_H2}'>&#128202; 1. Seuils et critères</h2>
<table style='{_TABLE}'>
<tr><th style='{_TH}'>Paramètre</th><th style='{_TH}'>Seuil</th><th style='{_TH}'>Signification</th></tr>
<tr><td style='{_TD}'><b>IAH</b></td><td style='{_TD}'>&lt; 5/h</td><td style='{_TD}'>Normal</td></tr>
<tr><td style='{_TD}'><b>IAH</b></td><td style='{_TD}'>5–14/h</td><td style='{_TD}'>SAHOS léger</td></tr>
<tr><td style='{_TD}'><b>IAH</b></td><td style='{_TD}'>15–29/h</td><td style='{_TD}'>SAHOS modéré</td></tr>
<tr><td style='{_TD}'><b>IAH</b></td><td style='{_TD}'>≥ 30/h</td><td style='{_TD}'>SAHOS sévère</td></tr>
<tr><td style='{_TD}'><b>Diagnostic</b></td><td style='{_TD}'>IAH ≥ 5/h + symptômes</td><td style='{_TD}'>SAHOS affirmé (HAS 2023)</td></tr>
<tr><td style='{_TD}'><b>Durée d'analyse</b></td><td style='{_TD}'>≥ 4 h</td><td style='{_TD}'>En dessous : non concluant (SFARS)</td></tr>
<tr><td style='{_TD}'><b>PLM</b></td><td style='{_TD}'>≥ 15/h</td><td style='{_TD}'>Pathologique (SJSR si plainte)</td></tr>
<tr><td style='{_TD}'><b>Epworth</b></td><td style='{_TD}'>≥ 11/24</td><td style='{_TD}'>Somnolence diurne excessive</td></tr>
<tr><td style='{_TD}'>BOSS</td><td style='{_TD}'>≥ 3/8</td><td style='{_TD}'>Risque accidentogène</td></tr>
<tr><td style='{_TD}'><b>SpO2 minimale</b></td><td style='{_TD}'>&lt; 80 %</td><td style='{_TD}'>Désaturation profonde</td></tr>
<tr><td style='{_TD}'><b>T90</b></td><td style='{_TD}'>≥ 15 %</td><td style='{_TD}'>Hypoxémie sévère</td></tr>
</table>

<h2 style='{_H2}'>&#128138; 2. Remboursement des dispositifs (LPP)</h2>
<div style='{_CARD}'>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>PPC</b> : IAH ≥ 30/h (avec ou sans comorbidités), <b>ou</b> IAH 15–30/h <b>avec</b> comorbidités.</li>
<li style='{_LI}'><b>OAM</b> : IAH 15–30/h <b>sans</b> comorbidités, ou refus de la PPC.</li>
<li style='{_LI}'><b>IAH &lt; 15/h</b> : pas de prise en charge — hygiène du sommeil, perte de poids, réévaluation si aggravation.</li>
<li style='{_LI}'><b>Avant OAM</b> : contre-indications dentaires — édentation étendue, troubles de l'ATM, parodontopathie active.</li>
<li style='{_LI}'><b>Observance PPC</b> : ≥ 4 h/nuit sur 70 % des nuits à 4 mois, sinon réévaluation.</li>
</ul>
</div>

<h2 style='{_H2}'>&#9881;&#65039; 3. Workflow Nox Journal — ce qui n'est PAS automatique</h2>
<div style='{_CARD}'>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>1. Analyse automatique brute</b> → toujours relire et corriger les événements mal détectés (flux nasal, oxymétrie).</li>
<li style='{_LI}'><b>2. Analyse des stades (Nox Body Sleep)</b> → à lancer pour obtenir éveil/NREM/REM, l'IAH REM, la fragmentation et le temps de sommeil.</li>
<li style='{_LI}'><b>3. Analyse « respiration de Cheyne-Stokes »</b> → à lancer <b>manuellement</b> si des apnées centrales sont détectées — indispensable avant de conclure à un syndrome d'apnées centrales.</li>
<li style='{_LI}'><b>4. Export PDF</b> après relecture : c'est ce PDF qui est importé dans Somnox.</li>
</ul>
</div>

<h2 style='{_H2}'>&#9888;&#65039; 4. Pièges d'interprétation</h2>
<div style='{_CARD}'>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>Sous-estimation</b> : la polygraphie (sans EEG) sous-estime l'IAH vs polysomnographie — un résultat limite n'exclut pas le diagnostic.</li>
<li style='{_LI}'><b>Discordance IAH/IDO</b> marquée → vérifier le flux nasal (fuite, respiration buccale) et l'oxymétrie.</li>
<li style='{_LI}'><b>Prédominance centrale</b> → rechercher insuffisance cardiaque, ACFA ; prudence avant PPC (apnées centrales émergentes) ; penser Cheyne-Stokes.</li>
<li style='{_LI}'><b>Obésité + hypoxémie nocturne</b> → gaz du sang diurnes (syndrome d'obésité-hypoventilation).</li>
<li style='{_LI}'><b>Somnolence avec IAH normal</b> → SHVAS, narcolepsie, SJSR, dette de sommeil, hypothyroïdie, dépression.</li>
<li style='{_LI}'><b>SAHOS positionnel</b> (dorsal/non-dorsal ≥ 2) → dispositif anti-dorsal, surtout si IAH normal en latéral.</li>
<li style='{_LI}'><b>SAHOS REM</b> → surveiller l'aggravation avec l'âge et le poids.</li>
<li style='{_LI}'><b>Contrôle sous OAM/PPC</b> → comparer aux valeurs pré-traitement et évaluer les symptômes <b>sous</b> traitement, pas les symptômes initiaux.</li>
</ul>
</div>

<h2 style='{_H2}'>&#128663; 5. Conduite automobile (arrêté révisé du 28 mars 2022)</h2>
<div style='{_CARD}'>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>SAHOS + somnolence</b> = incapacité incompatible avec le permis : information du patient, déclaration de sa propre initiative à la commission départementale des permis de conduire ou à un médecin agréé.</li>
<li style='{_LI}'><b>Reprise de la conduite</b> : réévaluation clinique ≥ 1 mois de traitement efficace + Test de Maintien d'Éveil (TME) — groupe léger : tous les 3 ans ; groupe lourd : tous les ans.</li>
</ul>
</div>

<h2 style='{_H2}'>&#128301; 6. Critères d'analyse AASM 2023</h2>
<div style='{_CARD}'>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>Apnée</b> : diminution de plus de 90 % du flux nasal pendant au moins 10 secondes.</li>
<li style='{_LI}'><b>Hypopnée</b> : diminution de plus de 30 % du flux nasal associée à une désaturation d'au moins 3 %.</li>
</ul>
</div>

<h2 style='{_H2}'>&#128230; 7. Suivi par situation</h2>
<table style='{_TABLE}'>
<tr><th style='{_TH}'>Situation</th><th style='{_TH}'>Suivi</th></tr>
<tr><td style='{_TD}'>Mise en place OAM</td><td style='{_TD}'>Contrôle polygraphique à 4 mois (efficacité, tolérance, calage dentaire)</td></tr>
<tr><td style='{_TD}'>OAM efficace</td><td style='{_TD}'>Contrôle à 12 mois ou si aggravation</td></tr>
<tr><td style='{_TD}'>Mise en place PPC</td><td style='{_TD}'>Consultation à 4 mois (observance ≥ 4 h/nuit sur 70 % des nuits)</td></tr>
<tr><td style='{_TD}'>SAHOS léger non appareillé</td><td style='{_TD}'>Pas de RDV systématique — disposition si aggravation (nycturie, somnolence, asthénie, ronflements, céphalées)</td></tr>
<tr><td style='{_TD}'>Somnolence non expliquée</td><td style='{_TD}'>Polysomnographie à discuter</td></tr>
</table>
"""


def guide_html() -> str:
    return GUIDE_HTML
