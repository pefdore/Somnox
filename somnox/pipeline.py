"""Pipeline complet : PDF -> texte -> parsing -> analyse -> documents."""

from __future__ import annotations

from pathlib import Path

from .analysis import AnalysisResult, analyse
from .generate import generate_all
from .models import PolygraphData
from .parser import parse_pdf


def process_pdf(pdf_path: str | Path, out_dir: str | Path, medecin: str = "") -> tuple[PolygraphData, AnalysisResult, dict]:
    data = parse_pdf(pdf_path)
    res = analyse(data)
    outputs = generate_all(data, res, out_dir, medecin)
    return data, res, outputs
