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

    p_watch = sub.add_parser("watch", help="Surveiller un dossier et traiter chaque nouveau PDF.")
    p_watch.add_argument("dossier")
    p_watch.add_argument("-o", "--out", default=None)
    p_watch.add_argument("-m", "--medecin", default="")

    p_gui = sub.add_parser("gui", help="Lancer l'interface graphique.")
    p_gui.add_argument("--watch", default=None, help="Dossier à surveiller au démarrage.")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.cmd == "run":
        from .pipeline import process_pdf

        _, res, outputs = process_pdf(args.pdf, args.out, args.medecin)
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

    if args.cmd == "gui":
        from .ui.app import run_app

        run_app(watch_dir=args.watch)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
