"""Read-only connectivity checks; load credentials exclusively from this root."""
from pathlib import Path
import hashlib
import base64
import ast
import json
import re
import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
GRID = "0x31C53838fF49168128D772625e34d3D2F7e11116"
ENDPOINTS = ["https://rpc.testnet-chain.genlayer.com", "https://studio.genlayer.com/api"]


def probe(url, method, params):
    try:
        response = requests.post(url, json={"jsonrpc":"2.0","id":1,"method":method,"params":params}, timeout=(10,25))
        report = {"http_status":response.status_code}
        if response.ok:
            obj = response.json()
            if "error" in obj:
                report["rpc_error_code"] = obj["error"].get("code")
            elif method == "eth_chainId":
                report["chain_id"] = int(obj["result"],16)
            elif isinstance(obj.get("result"), str):
                value = obj["result"]
                raw = bytes.fromhex(value[2:]) if value.startswith("0x") else value.encode() if value.startswith("#") else base64.b64decode(value,validate=True)
                report["returned_code_sha256"] = hashlib.sha256(raw).hexdigest()
                report["returned_code_bytes"] = len(raw)
                report["receipt_and_transfer_methods"] = [n.name for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and any(k in n.name for k in ("receipt","transfer","portfolio"))]
        return report
    except Exception as error:
        return {"error_type":type(error).__name__}


def main():
    env_path = ROOT/".env"
    if not env_path.is_file():
        print("Project .env is missing. Stop and ask the user.")
        return 1
    env = dotenv_values(env_path)
    credentials = {"project_env_exists":True, "github_token_present":bool(env.get("GITHUB_TOKEN")),
        "signing_key_count":sum(bool(v and re.fullmatch(r"(?:0x)?[0-9a-fA-F]{64}",v)) for k,v in env.items() if "PRIVATE_KEY" in k.upper())}
    report = {"credentials":credentials,"expected_chain_id":61999,"prophet_grid_address":GRID,
              "network_checks":[{"url":url, **probe(url,"eth_chainId",[])} for url in ENDPOINTS],
              "deployment_verified":False}
    studio = report["network_checks"][1]
    if studio.get("chain_id") == 61999:
        report["prophet_grid_code_probe"] = probe(ENDPOINTS[1],"gen_getContractCode",[GRID])
        public = requests.get("https://raw.githubusercontent.com/hoveiser/prophet-grid/main/contracts/prophet_grid.py",timeout=25)
        if public.ok:
            report["published_grid_source_sha256"] = hashlib.sha256(public.content).hexdigest()
            report["grid_source_matches_published"] = report["published_grid_source_sha256"] == report["prophet_grid_code_probe"].get("returned_code_sha256")
    out = ROOT/"evidence/preflight.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if studio.get("chain_id") == 61999 and report.get("prophet_grid_code_probe",{}).get("returned_code_bytes",0)>0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
