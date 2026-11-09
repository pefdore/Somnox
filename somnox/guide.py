"""Guide d'interprétation intégré — synthèse des recommandations (SFRMS/SFARS, HAS 2023)."""

_BLUE = "#0B57D0"
_DARK = "#041E49"
_TABLE = "border-collapse:collapse;width:100%;margin:8px 0;font-size:13px;"
_TH = f"background:{_BLUE};color:#FFFFFF;padding:7px 10px;text-align:left;"
_TD = "padding:6px 10px;border-bottom:1px solid #DDE3EA;"
_CARD = "background:#F8F9FF;border:1px solid #DDE3EA;border-radius:14px;padding:12px 16px;margin:10px 0;"
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
<tr><td style='{_TD}'><b>Charge hypoxique</b></td><td style='{_TD}'>≥ 50 %·min/h</td><td style='{_TD}'>Exposition hypoxique élevée (voir brief)</td></tr>
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

<h2 style='{_H2}'>&#128218; 8. Briefs d'interprétation</h2>

<div style='{_CARD}'>
<h3 style='color:{_DARK};margin:2px 0 6px 0;'>&#129514; Charge hypoxique (hypoxic burden)</h3>
<p style='margin:4px 0;'><b>Définition</b> : aire cumulée des désaturations sous la baseline de SpO2, rapportée à la durée de sommeil — exprimée en <b>%·min/h</b> dans Noxturnal. Elle quantifie l'<b>exposition hypoxique totale</b> de la nuit, là où la SpO2 minimale ne donne qu'un point isolé et le T90 un temps binaire.</p>
<p style='margin:4px 0;'><b>Pourquoi c'est utile</b> : deux patients avec le même IAH peuvent avoir des charges hypoxiques très différentes. La charge hypoxique intègre à la fois la profondeur, la durée et la répétition des désaturations. Les données de la littérature l'associent au risque cardiovasculaire (HTA, ACFA, mortalité cardiovasculaire), indépendamment de l'IAH.</p>
<p style='margin:4px 0;'><b>Comment l'interpréter</b> :</p>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>&lt; 20 %·min/h</b> : charge faible — retentissement hypoxique limité.</li>
<li style='{_LI}'><b>20–50 %·min/h</b> : charge notable — à corréler au T90, à la SpO2 minimale et aux comorbidités. Somnox la mentionne dans l'interprétation.</li>
<li style='{_LI}'><b>≥ 50 %·min/h</b> : charge élevée — Somnox génère une alerte : exposition cumulée importante, risque cardiovasculaire accru, argument pour un traitement efficace du SAHOS même si l'IAH est modéré.</li>
<li style='{_LI}'>À interpréter <b>en fonction du temps de sommeil</b> (une nuit courte majore l'indice horaire) et d'une éventuelle hypoxémie diurne (BPCO, SOH → gaz du sang).</li>
</ul>
</div>

<div style='{_CARD}'>
<h3 style='color:{_DARK};margin:2px 0 6px 0;'>&#127947; Respiration limitée vs Cheyne-Stokes : ne pas confondre</h3>
<p style='margin:4px 0;'><b>Cycles de respiration limitée</b> (flow limitation) : <b>phénomène obstructif</b> — le débit inspiratoire est aplati, diminué de moins de 30 % (donc ni apnée ni hypopnée au sens AASM), mais l'<b>effort respiratoire persiste</b> et augmente. C'est le signe d'une augmentation de résistance des voies aériennes supérieures. Le patient ronfle souvent, fait des efforts croissants, s'active (micro-éveils, AA) sans que l'IAH le montre.</p>
<p style='margin:4px 0;'><b>Respiration de Cheyne-Stokes</b> : <b>phénomène central</b> — respiration périodique en crescendo-décrescendo du volume courant, entrecoupée d'apnées/hypopnées <b>sans effort respiratoire</b>. On la recherche dans l'insuffisance cardiaque, après un AVC, dans l'insuffisance rénale ou sous opioïdes.</p>
<table style='{_TABLE}'>
<tr><th style='{_TH}'>Critère</th><th style='{_TH}'>Respiration limitée</th><th style='{_TH}'>Cheyne-Stokes</th></tr>
<tr><td style='{_TD}'>Mécanisme</td><td style='{_TD}'>Obstructif (VAS)</td><td style='{_TD}'>Central (commande)</td></tr>
<tr><td style='{_TD}'>Effort respiratoire</td><td style='{_TD}'>Présent, croissant</td><td style='{_TD}'>Absent pendant l'événement</td></tr>
<tr><td style='{_TD}'>Morphologie du flux</td><td style='{_TD}'>Aplatissement inspiratoire</td><td style='{_TD}'>Crescendo-décrescendo périodique</td></tr>
<tr><td style='{_TD}'>Contexte</td><td style='{_TD}'>Ronflement, SHVAS, SAHOS débutant</td><td style='{_TD}'>IC, AVC, opioïdes, insuffisance rénale</td></tr>
<tr><td style='{_TD}'>Conduite à tenir</td><td style='{_TD}'>Si somnolence + IAH bas : PSG (SHVAS) ; perte de poids</td><td style='{_TD}'>Bilan cardiologique (ETT, BNP), avis spécialisé, prudence PPC</td></tr>
</table>
<p style='margin:4px 0;'><b>Points clés</b> :</p>
<ul style='margin:4px 0;'>
<li style='{_LI}'>Dans Nox Journal, l'analyse Cheyne-Stokes est <b>manuelle</b> : si des apnées centrales sont détectées, <b>lancez-la avant de conclure</b> (Somnox vous le rappelle dans la checklist).</li>
<li style='{_LI}'>Cycles de respiration limitée ≥ 10 % de la nuit + somnolence avec IAH peu élevé → évoquer un <b>SHVAS</b> (Somnox le propose dans les diagnostics différentiels).</li>
<li style='{_LI}'>Cheyne-Stokes confirmé → pas de PPC systématique (risque d'apnées centrales émergentes) : avis spécialisé, traitement de la cause, discuter ASV selon le contexte cardiologique.</li>
</ul>
</div>

<div style='{_CARD}'>
<h3 style='color:{_DARK};margin:2px 0 6px 0;'>&#128147; Activations autonomiques (AA)</h3>
<p style='margin:4px 0;'><b>Définition</b> : activations transitoires du système nerveux autonome (réponse sympathique) détectées sur les variations du signal de pléthysmographie/pouls — accélération brève du rythme cardiaque contemporaine d'un événement respiratoire. Sur polygraphie <b>sans EEG</b>, c'est le <b>traceur indirect de la fragmentation</b> du sommeil : là où la polysomnographie mesure directement les micro-éveils (index d'arousals), la polygraphie s'appuie sur ces AA.</p>
<p style='margin:4px 0;'><b>Comment interpréter</b> :</p>
<ul style='margin:4px 0;'>
<li style='{_LI}'><b>AA proche de l'IAH</b> : chaque événement respiratoire s'accompagne d'une activation — cohérent, la fragmentation est le retentissement attendu du SAHOS.</li>
<li style='{_LI}'><b>AA très élevées (&gt; 30/h)</b> : fragmentation importante, retentissement diurne probable même si l'IAH paraît modéré — Somnox le souligne dans l'interprétation.</li>
<li style='{_LI}'><b>AA élevées avec IAH normal</b> : la fragmentation n'est pas (que) respiratoire — penser PLM, respiration limitée/SHVAS, douleur, environnement (Somnox oriente vers les diagnostics différentiels).</li>
<li style='{_LI}'><b>AA basses malgré un IAH élevé</b> : vérifier la qualité du signal de pouls (Somnox alerte si qualité &lt; 60 %) ; l'absence d'activation peut aussi refléter une atténuation autonomique (diabète, âge, traitements) — interpréter avec prudence.</li>
<li style='{_LI}'>L'index d'AA ne remplace pas l'EEG : il <b>surestime ou sous-estime</b> les micro-éveils réels ; c'est un marqueur de retentissement, pas un critère diagnostique.</li>
</ul>
</div>
"""


def guide_html() -> str:
    return GUIDE_HTML
