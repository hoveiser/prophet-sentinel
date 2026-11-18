"""Local release gates. Reports metadata only, never credential values."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/prophet_sentinel.py"
HEADER = '# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }'


def checks():
    raw = CONTRACT.read_bytes()
    source = raw.decode()
    ast.parse(source)
    ignored = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT).returncode == 0
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    secrets = []
    punctuation = []
    for name in filter(None, paths):
        path = ROOT / name
        if name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            secrets.append(name)
        if path.suffix not in {".py", ".ts", ".tsx", ".json", ".md", ".html", ".css", ".yml", ".txt"}:
            continue
        text = path.read_text()
        if "\u2014" in text:
            punctuation.append(name)
        if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|(?:PRIVATE_KEY|GITHUB_TOKEN)\s*=\s*[\"']?(?:0x)?[A-Za-z0-9_]{32,})", text):
            secrets.append(name)
    result = {"contract_bytes": len(raw), "under_37500_bytes": len(raw) < 37500,
              "sha256": hashlib.sha256(raw).hexdigest(), "pinned_header": source.splitlines()[0] == HEADER,
              "lf_only": b"\r" not in raw, "env_ignored": ignored,
              "suspected_secret_files": secrets, "public_em_dash_files": punctuation}
    print(json.dumps(result, indent=2))
    return all((result["under_37500_bytes"], result["pinned_header"], result["lf_only"], ignored, not secrets, not punctuation))


if __name__ == "__main__":
    raise SystemExit(0 if checks() else 1)
