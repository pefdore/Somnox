# Somnox

Application **hors ligne** d'aide à la rédaction des comptes rendus de polygraphie ventilatoire (noxT3s et rapports compatibles), pour la consultation de médecine du sommeil.

## Fonctionnalités

- **Import PDF** natif avec repli **OCR** (Tesseract, 300 dpi) pour les documents scannés.
- **Extraction** des paramètres clés : IAH, IA, IH, ODI, IAH positionnel/REM, SpO2 moyenne/minimale, T90, index de micro-éveils, PLM, ronflement, position, FC, IMC, Epworth.
- **Analyse experte** selon les recommandations françaises (SFARS/SFRMS, HAS 2023) : sévérité (IAH 5/15/30), fiabilité de l'enregistrement, composante positionnelle/REM, discordances IAH/ODI.
- **Points d'alerte** hiérarchisés : désaturation profonde (< 80 %), T90 ≥ 15 %, prédominance d'apnées centrales, tachycardie nocturne, Epworth ≥ 11, PLM ≥ 15/h, obésité.
- **Génération de 4 documents** (Markdown + DOCX) :
  - compte rendu de polygraphie ;
  - mémo récapitulatif praticien ;
  - points d'alerte du dossier ;
  - courrier au médecin traitant.
- **Dossier surveillé** (watchdog) : tout nouveau PDF y est analysé automatiquement.
- **Interface graphique** Material Design 3 (expressive), 100 % locale.

## Installation

Prérequis : Python ≥ 3.10 et [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) avec le paquet de langue `fra` (uniquement pour les PDF scannés).

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
