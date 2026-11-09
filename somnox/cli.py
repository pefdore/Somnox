"""Interface en ligne de commande : traitement ponctuel ou dossier surveillé."""

from __future__ import annotations

import argparse
import logging
import time


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="somnox", description="Analyse hors ligne de polygraphies ventilatoires.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Analyser un PDF et générer les documents.")
    p_run.add_argument("pdf")
    p_run.add_argument("-o", "--out", default="sorties")
    p_run.add_argument("-m", "--medecin", default="")
    p_run.add_argument("--epworth", type=int, default=None)
    p_run.add_argument("--boss", type=int, default=None, help="Score de BOSS (risque accidentogène)")
    p_run.add_argument("--comorbidites", default="", help="Séparées par des virgules (ex: HTA, diabète)")
    p_run.add_argument("--refus-ppc", action="store_true")
    p_run.add_argument("--symptomes", default="", help="somnolence,fatigue,nycturie,cephalees,ronflements")

    p_watch = sub.add_parser("watch", help="Surveiller un dossier et traiter chaque nouveau PDF.")
    p_watch.add_argument("dossier")
    p_watch.add_argument("-o", "--out", default=None)
    p_watch.add_argument("-m", "--medecin", default="")
    p_watch.add_argument("--epworth", type=int, default=None)
    p_watch.add_argument("--boss", type=int, default=None)
    p_watch.add_argument("--comorbidites", default="")
    p_watch.add_argument("--refus-ppc", action="store_true")

    p_setup = sub.add_parser("setup", help="Installer/vérifier Tesseract OCR (pack fra).")

    p_gui = sub.add_parser("gui", help="Lancer l'interface graphique.")
    p_gui.add_argument("--watch", default=None, help="Dossier à surveiller au démarrage.")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.cmd == "run":
        from .models import ClinicalContext
        from .pipeline import process_pdf

        symptomes = {s.strip() for s in args.symptomes.split(",") if s.strip()}
        ctx = ClinicalContext(
            epworth=args.epworth,
            boss=args.boss,
            comorbidites=[c.strip() for c in args.comorbidites.split(",") if c.strip()],
            refus_ppc=args.refus_ppc,
            somnolence="somnolence" in symptomes,
            fatigue="fatigue" in symptomes,
            nycturie="nycturie" in symptomes,
            cephees_matinales="cephalees" in symptomes,
            ronflements_constates="ronflements" in symptomes,
        )
        _, res, outputs = process_pdf(args.pdf, args.out, ctx, args.medecin)
        print(f"Sévérité : {res.severite}")
        for doc, paths in outputs.items():
            print(f"  {doc}: {paths['docx']}")
        return 0

    if args.cmd == "watch":
        from . import watcher

        observer = watcher.start(args.dossier, args.out, args.medecin)
        print("Surveillance active — Ctrl+C pour arrêter.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop(observer)
        return 0

    if args.cmd == "setup":
        from .setup import install_tesseract

        install_tesseract()
        return 0

    if args.cmd == "gui":
        from .ui.app import run_app

        run_app(watch_dir=args.watch)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
