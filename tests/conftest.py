"""Project-local SDK caches and temporary files only."""
from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
os.environ["HOME"] = str(ROOT)
os.environ["GENVM_VERSION"] = "v0.2.12"
TMP = ROOT / ".cache/tmp"
TMP.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TMP)
from gltest.direct import sdk_loader
sdk_loader.CACHE_DIR = ROOT / ".cache/genvm-linter"
