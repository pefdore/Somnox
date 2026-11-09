"""Installation guidée de Tesseract OCR (Windows / Linux / macOS) + pack fra."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import urllib.request

WINGET_ID = "UB-Mannheim.TesseractOCR"
FRA_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/fra.traineddata"

CMD_HELP = {
    "Windows": "winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements",
    "Linux": "sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-fra",
    "Darwin": "brew install tesseract tesseract-lang",
}


def tesseract_path() -> str | None:
    return shutil.which("tesseract")


def _fra_installed() -> bool:
    path = tesseract_path()
    if not path:
        return False
    try:
        langs = subprocess.run(
            [path, "--list-langs"], capture_output=True, text=True, timeout=15
        )
        return "fra" in (langs.stdout + langs.stderr).split()
    except Exception:
        return False


def _winget_fra() -> bool:
    """Sous winget, le paquet fra n'est pas inclus : télécharge fra.traineddata."""
    tessdir = shutil.which("tesseract")
    if not tessdir:
        return False
    import os

    tessdata = os.path.join(os.path.dirname(os.path.dirname(tessdir)), "tessdata")
    dest = os.path.join(tessdata, "fra.traineddata")
    if os.path.exists(dest):
        return True
    try:
        os.makedirs(tessdata, exist_ok=True)
        urllib.request.urlretrieve(FRA_URL, dest)
        return True
    except Exception:
        return False


def install_tesseract() -> None:
    print("=== Somnox — installation de Tesseract OCR ===\n")
    system = platform.system()

    if tesseract_path():
        print(f"[OK] Tesseract déjà installé : {tesseract_path()}")
    else:
        cmd = CMD_HELP.get(system)
        if not cmd:
            print(f"[!] Système non pris en charge automatiquement : {system}")
            print("    Installez Tesseract manuellement : https://github.com/tesseract-ocr/tesseract")
            sys.exit(1)
        print(f"[..] Tesseract absent — installation via : {cmd}")
        if system == "Windows":
            if not shutil.which("winget"):
                print("[!] winget indisponible. Installez « App Installer » depuis le Microsoft Store,")
                print("    ou téléchargez : https://github.com/UB-Mannheim/tesseract/wiki")
                sys.exit(1)
            subprocess.run(
                [
                    "winget", "install", "--id", WINGET_ID, "-e",
                    "--accept-source-agreements", "--accept-package-agreements",
                ],
                check=False,
            )
        else:
            print("    (exécutez la commande ci-dessus dans un terminal si elle échoue ici)")
            subprocess.run(cmd, shell=True, check=False)

    if tesseract_path() and not _fra_installed():
        print("[..] Pack de langue française (fra) manquant — installation…")
        if system == "Windows":
            if _winget_fra():
                print("[OK] fra.traineddata installé")
            else:
                print("[!] Téléchargez manuellement fra.traineddata :")
                print(f"    {FRA_URL}")
                print("    À placer dans le dossier tessdata de Tesseract.")
        else:
            subprocess.run("sudo apt-get install -y tesseract-ocr-fra", shell=True, check=False)

    print()
    if tesseract_path() and _fra_installed():
        print("[OK] Tesseract + pack fra opérationnels. Somnox est prêt pour l'OCR.")
    else:
        print("[!] Installation incomplète — relancez « somnox setup » après avoir refermé/rouvert")
        print("    le terminal (le PATH doit être rafraîchi).")
        sys.exit(1)
