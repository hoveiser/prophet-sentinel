"""Fetch the official pinned GenVM bundle into project-local caches."""
from pathlib import Path
import hashlib
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".cache/genvm-linter/genvm-universal-v0.2.12.tar.xz"
DIGEST = "4f0b358ec98ec148be9b95cdfb0f0e1a6cbe64da0194fdfac3fffc6f5d1d93e2"
ASSET = "https://api.github.com/repos/genlayerlabs/genvm/releases/assets/343376814"


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        with DEST.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == DIGEST
        print("Pinned SDK archive SHA-256 verified")
        return
    partial = DEST.with_suffix(".partial")
    response = requests.get(ASSET, headers={"Accept": "application/octet-stream"}, timeout=(20, 90), stream=True)
    response.raise_for_status()
    digest = hashlib.sha256()
    with partial.open("wb") as stream:
        for block in response.iter_content(1024 * 1024):
            stream.write(block)
            digest.update(block)
    if digest.hexdigest() != DIGEST:
        raise RuntimeError("SDK archive digest mismatch; archive not activated")
    partial.replace(DEST)
    print("Pinned SDK archive downloaded and SHA-256 verified")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("SDK bootstrap failed:", type(error).__name__)
        raise SystemExit(1)
