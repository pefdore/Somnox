# Somnox

Application **hors ligne** d'aide à la rédaction des comptes rendus de polygraphie ventilatoire (noxT3s et rapports compatibles), pour la consultation de médecine du sommeil.

## Fonctionnalités

- **Import PDF** natif avec repli **OCR** (Tesseract, 300 dpi) pour les documents scannés.
- **Extraction** des paramètres clés : IAH, IA, IH, IAHc/IAHo, ODI, IAH positionnel/REM, SpO2 moyenne/minimale, T90 (min et %), charge hypoxique, micro-éveils, PLM, ronflement (% et dBc), position, FC, IMC, Epworth, Pichot.
- **Contexte clinique** saisi dans l'app (symptômes, comorbidités, Epworth, BOSS, Pichot, refus de PPC) : il conditionne la proposition thérapeutique et le rappel réglementaire.
- **Analyse experte** selon les recommandations françaises (SFARS/SFRMS, HAS 2023) : sévérité (IAH 5/15/30), fiabilité de l'enregistrement, composante positionnelle/REM, discordances IAH/ODI.
- **Proposition thérapeutique conforme aux conditions de remboursement** : PPC si IAH ≥ 15/h avec comorbidités ou IAH ≥ 30/h ; OAM si IAH ≥ 15/h sans comorbidités (ou refus de la PPC).
- **Rappel de l'arrêté révisé du 28 mars 2022** (conduite automobile), avec la variante adaptée selon Epworth/BOSS.
- **Mémo « points de vigilance »** distinct : ce que vous auriez pu oublier, vigilance immédiate et à terme (BOSS manquant, comorbidités à vérifier, apnées centrales, PLM, nycturie, suivi pondéral, risque cardiovasculaire).
- **Points d'alerte** hiérarchisés : désaturation profonde (< 80 %), T90 ≥ 15 %, prédominance d'apnées centrales, tachycardie nocturne, Epworth ≥ 11, PLM ≥ 15/h, obésité.
- **Génération de 4 documents** (Markdown + DOCX) :
  - compte rendu de polygraphie ;
  - mémo récapitulatif praticien ;
  - points d'alerte du dossier ;
  - courrier au médecin traitant.
- **Dossier surveillé** (watchdog) : tout nouveau PDF y est analysé automatiquement.
- **Interface graphique** Material Design 3 (expressive), 100 % locale.

## Installation

Prérequis : Python ≥ 3.10. Tesseract OCR (pack `fra`, uniquement pour les PDF scannés) s'installe ensuite en une commande :

```bash
somnox setup
```

Sous Windows ceci utilise `winget` (installateur UB-Mannheim, pack `fra` téléchargé automatiquement), sous Linux `apt-get`, sous macOS `brew`. En cas d'échec, installation manuelle : [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) (cochez **French**).

```bash
pip install -r requirements.txt
pip install -e .
```

## Utilisation

Interface graphique :

```bash
somnox gui
```

Ligne de commande :

```bash
somnox run compte_rendu.pdf -o sorties        # analyse ponctuelle
somnox run cr.pdf --epworth 12 --boss 4 --comorbidites "HTA,diabète"
somnox watch ./a_surveiller                  # dossier surveillé
```

## Personnalisation

Les 4 documents sont produits à partir de gabarits Jinja2 modifiables dans `somnox/templates/` (`compte_rendu.j2`, `memo.j2`, `alertes.j2`, `courrier.j2`). Adaptez librement la structure de rédaction à votre pratique sans toucher au code.

## Avertissement

Outil d'aide à la décision : l'analyse produite doit être relue et validée par le praticien avant transmission. Ne remplace pas un enregistrement de référence (polysomnographie) lorsque celui-ci est indiqué.

## Tests

```bash
pip install pytest
pytest
```
