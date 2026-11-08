"""Interface graphique Somnox — Material Design 3 (expressive), 100 % hors ligne."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import watcher
from ..analysis import AnalysisResult, analyse
from ..generate import DOCS, generate_all
from ..models import COMORBIDITES_UI, SYMPTOMES_UI, ClinicalContext, PolygraphData
from ..parser import parse_pdf

THEME = Path(__file__).parent.parent / "theme.qss"


class MainWindow(QMainWindow):
    def __init__(self, watch_dir: str | None = None):
        super().__init__()
        self.setWindowTitle("Somnox — Analyse de polygraphie")
        self.resize(1100, 780)
        self.data: PolygraphData | None = None
        self.result: AnalysisResult | None = None
        self.observer = None
        self._build_ui()
        self._build_context_inputs()
        if watch_dir:
            self._start_watch(watch_dir)

    def _build_ui(self):
        root = QWidget(objectName="root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hero = QFrame(objectName="hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Somnox", objectName="appTitle")
        subtitle = QLabel("Polygraphie ventilatoire — lecture OCR & analyse experte hors ligne")
        subtitle.setContentsMargins(12, 0, 0, 0)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle, stretch=1)
        layout.addWidget(hero)

        actions = QHBoxLayout()
        self.btn_import = QPushButton("Importer un PDF")
        self.btn_import.clicked.connect(self._import_pdf)
        self.btn_watch = QPushButton("Dossier surveillé", objectName="secondary")
        self.btn_watch.clicked.connect(self._toggle_watch)
        self.btn_export = QPushButton("Exporter les documents")
        self.btn_export.clicked.connect(self._export)
        self.severity = QLabel("—", objectName="severity")
        self.severity.setAlignment(Qt.AlignCenter)
        actions.addWidget(self.btn_import)
        actions.addWidget(self.btn_watch)
        actions.addWidget(self.severity, stretch=1)
        actions.addWidget(self.btn_export)
        layout.addLayout(actions)

        self.tabs = QTabWidget()
        self.editors: dict[str, QPlainTextEdit] = {}
        titles = {
            "compte_rendu": "Compte rendu",
            "memo": "Mémo praticien",
            "alertes": "Points d'alerte",
            "courrier": "Courrier MT",
        }
        for doc in DOCS:
            edit = QPlainTextEdit()
            edit.setReadOnly(True)
            self.editors[doc] = edit
            self.tabs.addTab(edit, titles[doc])
        layout.addWidget(self.tabs, stretch=1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Prêt — aucun examen chargé.")
        self.setCentralWidget(root)

    def _build_context_inputs(self):
        """Panneau de contexte clinique : symptômes, comorbidités, BOSS, Epworth."""
        from PySide6.QtWidgets import QCheckBox, QGroupBox, QSpinBox

        self.ctx_group = QGroupBox("Contexte clinique (absent du PDF)")
        grid = QHBoxLayout(self.ctx_group)

        sympt_box = QVBoxLayout()
        self.chk_sympt = {}
        for key, label in SYMPTOMES_UI.items():
            cb = QCheckBox(label)
            self.chk_sympt[key] = cb
            sympt_box.addWidget(cb)

        comorb_box = QVBoxLayout()
        self.chk_comorb = {}
        for label in COMORBIDITES_UI:
            cb = QCheckBox(label)
            self.chk_comorb[label] = cb
            comorb_box.addWidget(cb)

        scores = QVBoxLayout()
        self.spin_epworth = QSpinBox(); self.spin_epworth.setRange(0, 24); self.spin_epworth.setSpecialValueText("Epworth —")
        self.spin_boss = QSpinBox(); self.spin_boss.setRange(0, 10); self.spin_boss.setSpecialValueText("BOSS —")
        self.spin_pichot = QSpinBox(); self.spin_pichot.setRange(0, 40); self.spin_pichot.setSpecialValueText("Pichot —")
        self.chk_refus_ppc = QCheckBox("Refus de la PPC")
        for w in (self.spin_epworth, self.spin_boss, self.spin_pichot, self.chk_refus_ppc):
            scores.addWidget(w)

        grid.addLayout(sympt_box)
        grid.addLayout(comorb_box)
        grid.addLayout(scores)
        self.centralWidget().layout().insertWidget(2, self.ctx_group)

    def _current_context(self) -> ClinicalContext:
        epworth = self.spin_epworth.value() if self.spin_epworth.value() > 0 else None
        boss = self.spin_boss.value() if self.spin_boss.value() > 0 else None
        pichot = self.spin_pichot.value() if self.spin_pichot.value() > 0 else None
        return ClinicalContext(
            epworth=epworth,
            boss=boss,
            pichot=pichot,
            comorbidites=[k for k, cb in self.chk_comorb.items() if cb.isChecked()],
            refus_ppc=self.chk_refus_ppc.isChecked(),
            **{k: cb.isChecked() for k, cb in self.chk_sympt.items()},
        )

    # ---------------------------------------------------------------- actions

    def _import_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un compte rendu de polygraphie", "", "PDF (*.pdf)"
        )
        if not path:
            return
        self.status.showMessage(f"Lecture : {Path(path).name} …")
        try:
            self.data = parse_pdf(path)
            if self.data.epworth is not None:
                self.spin_epworth.setValue(self.data.epworth)
            if self.data.pichot is not None:
                self.spin_pichot.setValue(self.data.pichot)
            self.result = analyse(self.data, self._current_context())
            self._display()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Échec de l'import :\n{exc}")
            self.status.showMessage("Échec de l'import.")

    def _toggle_watch(self):
        if self.observer:
            watcher.stop(self.observer)
            self.observer = None
            self.btn_watch.setText("Dossier surveillé")
            self.status.showMessage("Surveillance arrêtée.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Dossier à surveiller")
        if folder:
            self._start_watch(folder)

    def _start_watch(self, folder: str):
        out = Path(folder).parent / "sorties"
        self.observer = watcher.start(folder, out)
        self.btn_watch.setText("Arrêter la surveillance")
        self.status.showMessage(f"Surveillance : {folder} → {out}")

    def _export(self):
        if not self.data or not self.result:
            QMessageBox.information(self, "Export", "Importez d'abord un examen.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Dossier d'export")
        if not folder:
            return
        outputs = generate_all(self.data, self.result, folder, self._current_context())
        self.status.showMessage(f"Documents générés dans {folder}")
        QMessageBox.information(
            self, "Export", "\n".join(p["docx"] for p in outputs.values())
        )

    # ---------------------------------------------------------------- rendu

    def _display(self):
        from ..generate import render

        assert self.data and self.result
        self.result = analyse(self.data, self._current_context())
        self.severity.setText(self.result.severite)
        self.severity.setProperty("sev", self.result.severite)
        self.severity.style().unpolish(self.severity)
        self.severity.style().polish(self.severity)
        for doc in DOCS:
            self.editors[doc].setPlainText(render(doc, self.data, self.result, self._current_context()))
        self.status.showMessage(
            f"Examen chargé ({self.data.methode_extraction}) — {self.data.patient or 'patient inconnu'}"
        )


def run_app(watch_dir: str | None = None) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(THEME.read_text(encoding="utf-8"))
    win = MainWindow(watch_dir=watch_dir)
    win.show()
    app.exec()
