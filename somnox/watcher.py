"""Surveillance d'un dossier : traite automatiquement tout nouveau PDF."""

from __future__ import annotations

import logging
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .pipeline import process_pdf

log = logging.getLogger("somnox.watcher")


class _PdfHandler(FileSystemEventHandler):
    def __init__(self, watch_dir: Path, out_dir: Path, medecin: str = ""):
        self.watch_dir = Path(watch_dir)
        self.out_dir = Path(out_dir)
        self.medecin = medecin

    def on_created(self, event):
        self._handle(event)

    def on_moved(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        path = Path(event.dest_path if hasattr(event, "dest_path") and event.dest_path else event.src_path)
        if path.suffix.lower() != ".pdf":
            return
        log.info("Nouveau PDF détecté : %s", path)
        try:
            _, res, outputs = process_pdf(path, self.out_dir, self.medecin)
            log.info("Traité (%s) : %s", res.severite, outputs.get("compte_rendu", {}).get("docx"))
        except Exception:
            log.exception("Échec du traitement de %s", path)


def start(watch_dir: str | Path, out_dir: str | Path | None = None, medecin: str = "") -> Observer:
    watch_dir = Path(watch_dir).resolve()
    out_dir = Path(out_dir or (watch_dir.parent / "sorties")).resolve()
    watch_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(_PdfHandler(watch_dir, out_dir, medecin), str(watch_dir), recursive=False)
    observer.start()
    log.info("Surveillance active : %s -> %s", watch_dir, out_dir)
    return observer


def stop(observer: Observer) -> None:
    observer.stop()
    observer.join()
