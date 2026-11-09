"""Guide d'interprétation intégré — synthèse des recommandations (SFRMS/SFARS, HAS 2023)."""

GUIDE_HTML = """
<h2>Seuils et critères</h2>
<table cellspacing='6'>
<tr><th>Paramètre</th><th>Seuil</th><th>Signification</th></tr>
<tr><td>IAH</td><td>&lt; 5/h</td><td>Normal</td></tr>
<tr><td>IAH</td><td>5–14/h</td><td>SAHOS léger</td></tr>
<tr><td>IAH</td><td>15–29/h</td><td>SAHOS modéré</td></tr>
<tr><td>IAH</td><td>≥ 30/h</td><td>SAHOS sévère</td></tr>
<tr><td>Diagnostic</td><td>IAH ≥ 5/h + symptômes</td><td>SAHOS affirmé (HAS 2023)</td></tr>
<tr><td>Durée d'analyse</td><td>≥ 4 h</td><td>En dessous : non concluant</td></tr>
<tr><td>PLM</td><td>≥ 15/h</td><td>Pathologique (SJSR si plainte)</td></tr>
<tr><td>Epworth</td><td>≥ 11/24</td><td>Somnolence diurne excessive</td></tr>
<tr><td>BOSS</td><td>≥ 3</td><td>Risque accidentogène</td></tr>
</table>

<h2>Remboursement des dispositifs (LPP)</h2>
<ul>
<li><b>PPC</b> : IAH ≥ 30/h (avec ou sans comorbidités), ou IAH 15–30/h <b>avec</b> comorbidités.</li>
<li><b>OAM</b> : IAH 15–30/h <b>sans</b> comorbidités, ou refus de la PPC.</li>
<li>IAH &lt; 15/h : pas de prise en charge — hygiène de sommeil, perte de poids, réévaluation.</li>
<li>Avant OAM : vérifier contre-indications dentaires (édentation, ATM, parodontopathie).</li>
</ul>

<h2>Workflow Nox Journal — ce qui n'est PAS automatique</h2>
<ul>
<li><b>Relecture manuelle des signaux</b> : l'analyse automatique est brute ; corriger les événements mal détectés.</li>
<li><b>Analyse des stades (Nox Body Sleep)</b> : à lancer pour obtenir éveil/NREM/REM, l'IAH REM et la fragmentation.</li>
<li><b>Analyse « respiration de Cheyne-Stokes »</b> : à lancer manuellement si des apnées centrales sont détectées — indispensable avant de conclure à un syndrome d'apnées centrales.</li>
<li>Export PDF après relecture : c'est ce PDF qui est importé dans Somnox.</li>
</ul>

<h2>Pièges d'interprétation</h2>
<ul>
<li>La polygraphie (sans EEG) <b>sous-estime</b> l'IAH vs polysomnographie : un résultat limite n'exclut pas le diagnostic.</li>
<li>Discordance IAH/IDO marquée → vérifier le flux nasal (fuite, respiration buccale) et l'oxymétrie.</li>
<li>Prédominance centrale → rechercher insuffisance cardiaque, ACFA ; prudence avant PPC (apnées centrales émergentes).</li>
<li>Obésité + hypoxémie nocturne → gaz du sang diurnes (syndrome d'obésité-hypoventilation).</li>
<li>Somnolence avec IAH normal → SHVAS, narcolepsie, SJSR, dette de sommeil, hypothyroïdie, dépression.</li>
<li>Contrôle sous OAM/PPC : comparer aux valeurs pré-traitement et évaluer les symptômes <b>sous</b> traitement.</li>
</ul>

<h2>Conduite automobile (arrêté révisé du 28 mars 2022)</h2>
<ul>
<li>SAHOS + somnolence = incapacité incompatible avec le permis : information du patient, déclaration à la commission départementale ou à un médecin agréé.</li>
<li>Reprise de la conduite : réévaluation clinique ≥ 1 mois de traitement efficace + TME (groupe léger : tous les 3 ans ; groupe lourd : tous les ans).</li>
</ul>

<h2>Critères d'analyse AASM 2023</h2>
<ul>
<li>Apnée : diminution de plus de 90 % du flux nasal pendant au moins 10 secondes.</li>
<li>Hypopnée : diminution de plus de 30 % du flux nasal associée à une désaturation d'au moins 3 %.</li>
</ul>
"""


def guide_html() -> str:
    return GUIDE_HTML
