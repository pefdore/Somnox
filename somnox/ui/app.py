"""Interface graphique Somnox — Material Design 3 (expressive), 100 % hors ligne."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
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
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import watcher
from ..analysis import AnalysisResult, analyse
from ..generate import DOCS, generate_all
from ..report_html import alertes_html, memo_html
from ..context import build_context
from ..models import COMORBIDITES_UI, SYMPTOMES_UI, TYPE_EXAMEN_LABELS, ClinicalContext, PolygraphData
from ..parser import parse_pdf

THEME = Path(__file__).parent.parent / "theme.qss"


class PdfPreview(QScrollArea):
    """Aperçu PDF : pages toujours ajustées à la largeur de la zone, zoom molette Ctrl + pinch."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self._zoom = 1.0
        self._pixmaps: list = []
        self._labels: list[QLabel] = []
        self.pages = QWidget()
        self._layout = QVBoxLayout(self.pages)
        self._layout.setSpacing(12)
        self._layout.addStretch(1)
        self.setWidget(self.pages)
        self.viewport().installEventFilter(self)
        self.grabGesture(Qt.PinchGesture)

    def clear(self) -> None:
        self._pixmaps.clear()
        self._labels.clear()
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load(self, path: str) -> None:
        import pymupdf

        self.clear()
        try:
            doc = pymupdf.open(path)
        except Exception as exc:
            self._layout.insertWidget(0, QLabel(f"Erreur : {exc}"))
            return
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            self._pixmaps.append(QPixmap.fromImage(img))
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            self._labels.append(lbl)
            self._layout.insertWidget(self._layout.count() - 1, lbl)
        doc.close()
        self.rescale()

    def rescale(self) -> None:
        if not self._pixmaps:
            return
        width = max(int((self.viewport().width() - 24) * self._zoom), 100)
        for pm, lbl in zip(self._pixmaps, self._labels):
            lbl.setPixmap(pm.scaledToWidth(width, Qt.SmoothTransformation))
        self.pages.adjustSize()

    def eventFilter(self, obj, event):
        if obj is self.viewport() and event.type() == event.Type.Resize:
            self.rescale()
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._zoom = max(0.3, min(5.0, self._zoom * (1.1 if event.angleDelta().y() > 0 else 0.9)))
            self.rescale()
        else:
            super().wheelEvent(event)

    def event(self, event):
        if event.type() == event.Type.Gesture:
            gesture = event.gesture(Qt.PinchGesture)
            if gesture:
                self._zoom = max(0.3, min(5.0, self._zoom * gesture.scaleFactor()))
                self.rescale()
                return True
        return super().event(event)


class MainWindow(QMainWindow):
    def __init__(self, watch_dir: str | None = None):
        super().__init__()
        self.setWindowTitle("Somnox — Analyse de polygraphie")
        self.resize(1100, 780)
        self.data: PolygraphData | None = None
        self.result: AnalysisResult | None = None
        self.observer = None
        self.pdf_path: str | None = None
        self._build_ui()
        self._build_context_inputs()
        if watch_dir:
            self._start_watch(watch_dir)

    def _build_ui(self):
        root = QWidget(objectName="root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self._root_layout = layout

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
        self.editors: dict[str, QWidget] = {}
        titles = {
            "compte_rendu": "Compte rendu",
            "memo": "Mémo praticien",
            "alertes": "Points d'alerte",
            "courrier": "Courrier MT",
        }
        for doc in DOCS:
            if doc in ("memo", "alertes"):
                edit = QTextBrowser()
                edit.setOpenExternalLinks(False)
            else:
                edit = QPlainTextEdit()
                edit.setReadOnly(True)
            self.editors[doc] = edit
            self.tabs.addTab(edit, titles[doc])
        layout.addWidget(self.tabs, stretch=1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Prêt — aucun examen chargé.")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(root)
        splitter.addWidget(self._build_preview())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([3000, 1000])
        self.setCentralWidget(splitter)

    def _build_preview(self) -> QWidget:
        """Panneau droit : aperçu du PDF importé (25 % de la largeur, zoomable)."""
        panel = QFrame(objectName="previewPanel")
        box = QVBoxLayout(panel)
        box.setContentsMargins(8, 8, 8, 8)
        box.setSpacing(6)
        header = QLabel("PDF importé — Ctrl+molette / pinch pour zoomer", objectName="previewTitle")
        header.setWordWrap(True)
        self.preview_name = QLabel("Aucun document")
        self.preview_name.setWordWrap(True)
        self.preview = PdfPreview()
        box.addWidget(header)
        box.addWidget(self.preview_name)
        box.addWidget(self.preview, stretch=1)
        return panel

    def _show_pdf(self, path: str) -> None:
        self.preview_name.setText(Path(path).name)
        self.preview.load(path)

    def _build_context_inputs(self):
        """Panneau de contexte clinique : symptômes, comorbidités, BOSS, Epworth."""
        from PySide6.QtWidgets import QCheckBox, QComboBox, QGroupBox, QSpinBox

        self.ctx_group = QGroupBox("Contexte clinique — pré-rempli depuis les Indications, ajustable")
        grid = QHBoxLayout(self.ctx_group)

        type_box = QVBoxLayout()
        self.combo_type = QComboBox()
        self.combo_type.addItems(list(TYPE_EXAMEN_LABELS.values()))
        type_box.addWidget(QLabel("Type d'examen :"))
        type_box.addWidget(self.combo_type)
        type_box.addStretch(1)
        grid.addLayout(type_box)

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
        self._root_layout.insertWidget(2, self.ctx_group)

    def _current_context(self) -> ClinicalContext:
        epworth = self.spin_epworth.value() if self.spin_epworth.value() > 0 else None
        boss = self.spin_boss.value() if self.spin_boss.value() > 0 else None
        pichot = self.spin_pichot.value() if self.spin_pichot.value() > 0 else None
        type_key = next(
            (k for k, lbl in TYPE_EXAMEN_LABELS.items() if lbl == self.combo_type.currentText()),
            "primo",
        )
        return ClinicalContext(
            epworth=epworth,
            boss=boss,
            pichot=pichot,
            type_examen=type_key,
            comorbidites=[k for k, cb in self.chk_comorb.items() if cb.isChecked()],
            refus_ppc=self.chk_refus_ppc.isChecked(),
            **{k: cb.isChecked() for k, cb in self.chk_sympt.items()},
        )

    def _prefill_context(self, ctx: ClinicalContext) -> None:
        """Pré-remplit le panneau avec le contexte extrait des Indications."""
        self.combo_type.setCurrentText(TYPE_EXAMEN_LABELS.get(ctx.type_examen, TYPE_EXAMEN_LABELS["primo"]))
        if ctx.epworth is not None:
            self.spin_epworth.setValue(ctx.epworth)
        if ctx.boss is not None:
            self.spin_boss.setValue(ctx.boss)
        if ctx.pichot is not None:
            self.spin_pichot.setValue(ctx.pichot)
        for key, cb in self.chk_sympt.items():
            cb.setChecked(getattr(ctx, key, False))
        for label, cb in self.chk_comorb.items():
            cb.setChecked(label in ctx.comorbidites)

    # ---------------------------------------------------------------- actions

    def _import_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un compte rendu de polygraphie", "", "PDF (*.pdf)"
        )
        if not path:
            return
        self.pdf_path = path
        self._show_pdf(path)
        self.status.showMessage(f"Lecture : {Path(path).name} …")
        try:
            self.data = parse_pdf(path)
            self._prefill_context(build_context(self.data))
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
        ctx = self._current_context()
        for doc in DOCS:
            if doc == "memo":
                self.editors[doc].setHtml(memo_html(self.data, self.result, ctx))
            elif doc == "alertes":
                self.editors[doc].setHtml(alertes_html(self.data, self.result, ctx))
            else:
                self.editors[doc].setPlainText(render(doc, self.data, self.result, ctx))
        self.status.showMessage(
            f"Examen chargé ({self.data.methode_extraction}) — {self.data.patient or 'patient inconnu'}"
        )


def run_app(watch_dir: str | None = None) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(THEME.read_text(encoding="utf-8"))
    win = MainWindow(watch_dir=watch_dir)
    win.show()
    app.exec()
