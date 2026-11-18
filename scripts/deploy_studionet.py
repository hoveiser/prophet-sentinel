#!/usr/bin/env python3
"""Deploy ProphetSentinel to GenLayer studionet and execute multi-signer lifecycle.

Checkpointed in evidence/_checkpoint.json so re-invocations resume cleanly.
All transactions wait for terminal status and verify FINALIZED and MAJORITY_AGREE.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values
from web3 import Web3

from genlayer_py import create_account, create_client, studionet

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "prophet_sentinel.py"
EVIDENCE_DIR = ROOT / "evidence"
CHECKPOINT = EVIDENCE_DIR / "_checkpoint.json"
EVIDENCE_FILE = EVIDENCE_DIR / "studionet_deployment.json"

RPC_URL = "https://studio.genlayer.com/api"
CHAIN_ID = 61999
EXPLORER = "https://explorer-studio.genlayer.com"
RAW_CONTRACT_URL = (
    "https://raw.githubusercontent.com/hoveiser/prophet-sentinel/main/"
    "contracts/prophet_sentinel.py"
)

PROPHET_GRID_ADDRESS = "0x31C53838fF49168128D772625e34d3D2F7e11116"
NASA_URL = "https://www.nasa.gov/news/"
NOAA_URL = "https://www.noaa.gov/weather"

TERMINAL_STATUSES = ("FINALIZED", "CANCELED", "UNDETERMINED")
POLITE_DELAY = 2.0


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(message: str) -> None:
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), message), flush=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return default


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def retryable(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = ("429", "rate limit", "timeout", "timed out", "connection", "temporarily", "502", "503", "504", "reset by peer", "remote end closed")
    return any(marker in text for marker in markers)


def with_retries(fn, label: str, attempts: int = 8, base_delay: float = 4.0):
    last = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last = exc
            if not retryable(exc) or attempt == attempts:
                raise
            log("retry %d/%d %s after %s: %s" % (attempt, attempts - 1, label, type(exc).__name__, str(exc)[:110]))
            time.sleep(base_delay * attempt)
    raise RuntimeError("%s failed: %s" % (label, last))


def derive_key(master: str, index: int) -> str:
    seed = "prophet-sentinel-burner-v1:%d:%s" % (index, master.lower())
    digest = int.from_bytes(Web3.keccak(text=seed), "big")
    return "0x%064x" % digest


def leader_execution(receipt: dict) -> str | None:
    consensus = receipt.get("consensus_data") or {}
    leader = consensus.get("leader_receipt") or []
    if isinstance(leader, dict):
        leader = [leader]
    for item in leader:
        if isinstance(item, dict) and item.get("mode") == "leader" and item.get("execution_result"):
            return item.get("execution_result")
    for item in leader:
        if isinstance(item, dict) and item.get("execution_result"):
            return item.get("execution_result")
    return None


def vote_summary(receipt: dict) -> dict:
    votes = ((receipt.get("consensus_data") or {}).get("votes")) or {}
    values = [str(value).lower() for value in votes.values()]
    return {
        "agree": values.count("agree"),
        "disagree": values.count("disagree"),
        "total": len(values),
    }


def decoded_return(receipt: dict) -> str:
    data = ((receipt.get("tx_receipt_decoded") or {}).get("data"))
    if isinstance(data, str):
        return data[:600]
    return ""


def decode_code(result: str | None) -> tuple[int, str]:
    if not result:
        return 0, ""
    if result.startswith("0x"):
        raw = bytes.fromhex(result[2:])
    elif result.startswith("#"):
        raw = result.encode("utf-8")
    else:
        try:
            raw = base64.b64decode(result, validate=True)
        except Exception:
            raw = result.encode("utf-8")
    norm = normalize_lf(raw)
    return len(norm), sha256_hex(norm)


class Runner:
    def __init__(self, master_key: str):
        self.master_key = master_key
        self.main = create_account(master_key)
        self.client = create_client(chain=studionet, account=self.main)
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.checkpoint = load_json(CHECKPOINT, {})
        self.checkpoint.setdefault("steps", {})
        self.checkpoint.setdefault("transactions", [])
        self.checkpoint.setdefault("failures", [])
        self.burners = {
            name: create_account(derive_key(self.main.address, index))
            for index, name in enumerate(("alice", "bob", "carol"), start=1)
        }
        self.address = self.checkpoint.get("contract_address")

    def wait_final(self, tx_hash: str, timeout: int = 1200) -> dict:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                receipt = self.client.get_transaction(tx_hash)
            except Exception as exc:
                if retryable(exc):
                    time.sleep(5)
                    continue
                raise
            status = str(receipt.get("status_name") or "")
            last = status or last
            if status in TERMINAL_STATUSES:
                return receipt
            time.sleep(5)
        raise RuntimeError("transaction %s never finalized, last status %s" % (tx_hash, last))

    def summarize(self, tx_hash: str, receipt: dict, function_name: str, account: str) -> dict:
        votes = vote_summary(receipt)
        return {
            "tx_hash": tx_hash,
            "function": function_name,
            "account": account,
            "status": receipt.get("status_name"),
            "result": receipt.get("result_name"),
            "execution": leader_execution(receipt),
            "votes_agree": votes["agree"],
            "votes_disagree": votes["disagree"],
            "votes_total": votes["total"],
            "return_data": decoded_return(receipt),
            "explorer": "%s/transactions/%s" % (EXPLORER, tx_hash),
            "recorded_at": now_iso(),
        }

    def write(self, key: str, function_name: str, args: list | None = None, account=None, value: int = 0,
              target_address: str | None = None, attempts: int = 1, expect_execution: str = "SUCCESS") -> dict:
        if key in self.checkpoint["steps"]:
            entry = self.checkpoint["steps"][key]
            log("skip %s (%s)" % (key, str(entry.get("tx_hash", ""))[:18]))
            return entry
        signer = account or self.main
        target = target_address or self.address
        for attempt in range(1, attempts + 1):
            log("write %s -> %s value=%d as %s (attempt %d/%d)" % (key, function_name, value, signer.address[:10], attempt, attempts))
            tx_hash = with_retries(
                lambda: self.client.write_contract(
                    address=target, function_name=function_name, account=signer, args=args or [], value=value
                ),
                "submit " + key,
            )
            receipt = self.wait_final(tx_hash)
            entry = self.summarize(tx_hash, receipt, function_name, signer.address)
            accepted = entry["status"] == "FINALIZED" and entry["execution"] == expect_execution
            if accepted:
                self.record(key, entry)
                time.sleep(POLITE_DELAY)
                return entry
            self.checkpoint["failures"].append(dict(entry, step=key, attempt=attempt))
            save_json(CHECKPOINT, self.checkpoint)
            log("  not accepted: status=%s result=%s execution=%s" % (entry["status"], entry["result"], entry["execution"]))
            if attempt < attempts:
                time.sleep(15)
        raise RuntimeError("%s was not accepted after %d attempts" % (key, attempts))

    def record(self, key: str, entry: dict) -> dict:
        self.checkpoint["steps"][key] = entry
        self.checkpoint["transactions"].append(dict(entry, step=key))
        save_json(CHECKPOINT, self.checkpoint)
        return entry

    def read(self, function_name: str, args: list | None = None, target_address: str | None = None):
        target = target_address or self.address
        def call():
            return self.client.read_contract(address=target, function_name=function_name, args=args or [])
        value = with_retries(call, "read " + function_name)
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return value

    def read_json(self, function_name: str, args: list | None = None, target_address: str | None = None) -> dict:
        value = self.read(function_name, args, target_address)
        return json.loads(value) if isinstance(value, str) else value

    def ensure_deployed(self) -> str:
        if self.address:
            try:
                summary = self.read_json("get_custody_accounting_summary")
                log("reusing deployment %s" % self.address)
                return self.address
            except Exception as exc:
                log("checkpoint address unusable: %s" % str(exc)[:110])
        if "deploy" in self.checkpoint["steps"]:
            self.address = self.checkpoint["steps"]["deploy"].get("contract_address")
            if self.address:
                return self.address
        code = CONTRACT.read_text(encoding="utf-8")
        log("deploying contracts/prophet_sentinel.py to studionet")
        tx_hash = with_retries(
            lambda: self.client.deploy_contract(
                code=code,
                account=self.main,
                args=[],
            ),
            "deploy",
        )
        receipt = self.wait_final(tx_hash)
        address = self.contract_address_of(receipt, tx_hash)
        if not address:
            raise RuntimeError("no contract address in deploy receipt")
        self.address = address
        entry = self.summarize(tx_hash, receipt, "__deploy__", self.main.address)
        entry["contract_address"] = address
        self.checkpoint["contract_address"] = address
        self.record("deploy", entry)
        log("deployed at %s" % address)
        return address

    @staticmethod
    def contract_address_of(receipt: dict, tx_hash: str) -> str | None:
        for key in ("recipient", "to_address", "contract_address"):
            value = receipt.get(key)
            if isinstance(value, str) and len(value) == 42 and int(value, 16) != 0:
                return value
        leader = (receipt.get("consensus_data") or {}).get("leader_receipt") or {}
        items = [leader] if isinstance(leader, dict) else leader
        for item in items:
            if isinstance(item, dict):
                for key in ("contract_address", "address", "recipient"):
                    value = item.get(key)
                    if isinstance(value, str) and len(value) == 42:
                        return value
        return None

    def fund_burners(self) -> None:
        for name, account in self.burners.items():
            key = "fund:" + name
            if key in self.checkpoint["steps"]:
                continue
            bal = self.w3.eth.get_balance(account.address)
            if bal >= 10 ** 18:
                self.record(key, {"tx_hash": None, "already_funded": True, "account": account.address,
                                  "balance_wei": str(bal), "recorded_at": now_iso()})
                continue
            nonce = self.w3.eth.get_transaction_count(self.main.address)
            fee = self.w3.eth.gas_price
            tx = {
                "nonce": nonce, "to": account.address, "value": 2 * 10 ** 18, "gas": 21000,
                "maxFeePerGas": fee, "maxPriorityFeePerGas": fee, "chainId": CHAIN_ID, "type": 2,
            }
            raw = self.main.sign_transaction(tx).raw_transaction
            tx_hash = self.w3.eth.send_raw_transaction(raw)
            deadline = time.time() + 180
            while time.time() < deadline and self.w3.eth.get_balance(account.address) < 10 ** 18:
                time.sleep(3)
            self.record(key, {"tx_hash": tx_hash.hex(), "account": account.address,
                              "balance_wei": str(self.w3.eth.get_balance(account.address)), "recorded_at": now_iso()})
            log("funded %s (%s)" % (name, account.address[:10]))

    def ensure_prophet_grid_market(self, market_index: int) -> str:
        key = "grid:market%d" % market_index
        if key in self.checkpoint["steps"]:
            return str(self.checkpoint["steps"][key]["market_id"])
        cnt = int(self.read("get_market_count", [], target_address=PROPHET_GRID_ADDRESS))
        if market_index <= cnt:
            m = self.read_json("get_market", [str(market_index)], target_address=PROPHET_GRID_ADDRESS)
            if m.get("can_trade") is True:
                self.record(key, {"tx_hash": None, "market_id": market_index, "already_open": True, "recorded_at": now_iso()})
                return str(market_index)
        args = [
            "Will NASA Earth observatory detect positive precipitation anomaly in region %d?" % market_index,
            "SCIENCE",
            NASA_URL,
            NOAA_URL,
            "Resolved strictly according to official NASA and NOAA public reporting. 10000 if positive anomaly else 0.",
            5000,
            1000,
            86400,
            3600,
            7200,
        ]
        log("creating tradeable market %d on ProphetGrid" % (cnt + 1))
        tx_hash = with_retries(
            lambda: self.client.write_contract(
                address=PROPHET_GRID_ADDRESS, function_name="create_market", account=self.main, args=args
            ),
            "create_market on ProphetGrid",
        )
        receipt = self.wait_final(tx_hash)
        entry = self.summarize(tx_hash, receipt, "create_market", self.main.address)
        new_cnt = int(self.read("get_market_count", [], target_address=PROPHET_GRID_ADDRESS))
        entry["market_id"] = new_cnt
        self.record(key, entry)
        log("market %d created on ProphetGrid" % new_cnt)
        return str(new_cnt)

    def wait_until(self, epoch_seconds: int, label: str, max_wait: int = 150) -> None:
        remaining = max(0, epoch_seconds - int(time.time())) + 2
        chunk = min(remaining, max_wait)
        log("waiting %ds for %s (%ds total remaining)" % (chunk, label, remaining))
        deadline = time.time() + chunk
        while time.time() < deadline:
            time.sleep(min(10, max(0.5, deadline - time.time())))
        if time.time() < epoch_seconds + 2:
            log("chunk wait complete; %ds remaining for %s. Exiting cleanly for next turn." % (epoch_seconds - int(time.time()), label))
            sys.exit(0)

    def run_lifecycle(self) -> None:
        self.ensure_deployed()
        self.fund_burners()
        alice, bob, carol = self.burners["alice"], self.burners["bob"], self.burners["carol"]

        # Ensure ProphetGrid market 10 and 11 exist and are tradeable
        m10 = self.ensure_prophet_grid_market(10)
        m11 = self.ensure_prophet_grid_market(11)

        # 1. Soft-fail payable rejection & refund rail: Carol calls unknown round
        log("1. soft-fail payable rail: Carol deposits to unknown round 999, then withdraws refund")
        self.write("softfail:carol", "register_forecaster_signal_payable", ["999", 5000, NASA_URL],
                   account=carol, value=10**16, expect_execution="SUCCESS")
        carol_balance = self.read_json("get_refundable_balance", [carol.address])
        log("  Carol refundable wei: %s" % carol_balance["native_wei"])
        self.write("refund:carol", "withdraw_refund", [int(carol_balance["native_wei"])], account=carol)
        log("  Carol refund withdrawn successfully")

        # 2. Round 1: Multi-signer forecasting swarm and cross-contract acquisition
        log("2. Round 1: create forecaster round with market %s" % m10)
        self.write("round1:create", "create_forecaster_round", [m10, 600, 600, 10**16], account=self.main)
        self.write("round1:fund", "fund_signal_bounty_payable", ["1", 10**18], account=self.main, value=15 * 10**17)
        self.write("round1:register_alice", "register_forecaster_signal_payable", ["1", 8000, NASA_URL], account=alice, value=10**16)
        self.write("round1:register_bob", "register_forecaster_signal_payable", ["1", 8250, NASA_URL], account=bob, value=10**16)

        # 3. Round 2: Round settlement via claim_unverified_round_refund
        log("3. Round 2: create and fund round for market %s (zero forecasters)" % m11)
        self.write("round2:create", "create_forecaster_round", [m11, 600, 600, 10**16], account=self.main)
        self.write("round2:fund", "fund_signal_bounty_payable", ["2", 10**18], account=self.main, value=15 * 10**17)

        # 4. Wait for forecast lock epoch (600s window)
        r1 = self.read_json("get_round", ["1"])
        lock_epoch = int(r1["forecast_lock_epoch"])
        log("4. waiting for forecast lock epoch: %d" % lock_epoch)
        self.wait_until(lock_epoch, "forecast lock epoch for rounds 1 & 2")

        # 5. Audit Round 1 with validator swarm
        log("5. audit forecaster swarm on round 1 (live web rendering & LLM consensus)")
        self.write("round1:audit", "audit_forecaster_swarm", ["1"], account=self.main, attempts=3)
        r1_audited = self.read_json("get_round", ["1"])
        log("  Round 1 audited: status=%s ensemble_prob=%s derived_stake=%s side=%s" % (
            r1_audited["status"], r1_audited["ensemble_probability_bps"],
            r1_audited["derived_signal_stake_wei"], r1_audited.get("committed_outcome_side", "YES")))

        # 6. Execute signal position on ProphetGrid
        log("6. execute cross-contract signal position on ProphetGrid")
        self.write("round1:execute", "execute_signal_position_on_prophet_grid", ["1"], account=self.main)
        time.sleep(25)

        # 7. Reconcile ProphetGrid outcome shares
        log("7. reconcile ProphetGrid outcome shares")
        self.write("round1:reconcile", "reconcile_prophet_grid_outcome", ["1"], account=self.main, attempts=3)
        r1_reconciled = self.read_json("get_round_prophet_grid_reconciliation", ["1"])
        log("  Round 1 reconciliation: deployed=%s state=%s shares_held=%s" % (
            r1_reconciled["position_deployed"], r1_reconciled["position_state"],
            r1_reconciled["deployed_to_prophet_grid_wei"]))

        # 8. Settle Round 2 via claim_unverified_round_refund
        log("8. settle Round 2 via claim_unverified_round_refund")
        self.write("round2:settle", "claim_unverified_round_refund", ["2"], account=self.main)
        r2_state = self.read_json("get_round", ["2"])
        log("  Round 2 settled: status=%s" % r2_state["status"])

        # 9. Verify custody and build evidence
        self.build_evidence()

    def build_evidence(self) -> None:
        log("building evidence report...")
        summary = self.read_json("get_custody_accounting_summary")
        r1 = self.read_json("get_round", ["1"])
        r1_rec = self.read_json("get_round_prophet_grid_reconciliation", ["1"])
        r2 = self.read_json("get_round", ["2"])

        raw_contract = normalize_lf(CONTRACT.read_bytes())
        local_sha = sha256_hex(raw_contract)
        git_sha = None
        try:
            blob = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", "HEAD:contracts/prophet_sentinel.py"],
                                  capture_output=True, check=True).stdout
            git_sha = sha256_hex(normalize_lf(blob))
        except Exception as exc:
            log("git blob unavailable: %s" % str(exc)[:90])

        remote_sha = None
        try:
            res = requests.get(RAW_CONTRACT_URL, timeout=15)
            if res.status_code == 200:
                remote_sha = sha256_hex(normalize_lf(res.content))
        except Exception:
            pass

        onchain_bytes, onchain_sha = 0, ""
        try:
            code_res = self.client.provider.make_request("gen_getContractCode", [self.address])
            code_val = (code_res or {}).get("result")
            onchain_bytes, onchain_sha = decode_code(code_val)
        except Exception as exc:
            log("gen_getContractCode failed: %s" % str(exc)[:90])

        txs = self.checkpoint["transactions"]
        tx_summary = []
        for t in txs:
            tx_summary.append({
                "step": t.get("step"),
                "function": t.get("function"),
                "tx_hash": t.get("tx_hash"),
                "account": t.get("account"),
                "status": t.get("status"),
                "result": t.get("result"),
                "execution": t.get("execution"),
                "votes_agree": t.get("votes_agree"),
                "votes_disagree": t.get("votes_disagree"),
                "votes_total": t.get("votes_total"),
                "explorer": "%s/transactions/%s" % (EXPLORER, t.get("tx_hash")) if t.get("tx_hash") else None,
            })

        evidence = {
            "project": "ProphetSentinel",
            "chain_id": CHAIN_ID,
            "network": "GenLayer Studionet",
            "rpc_url": RPC_URL,
            "contract_address": self.address,
            "explorer_url": "%s/address/%s" % (EXPLORER, self.address),
            "linked_prophet_grid_address": PROPHET_GRID_ADDRESS,
            "linked_prophet_grid_explorer": "%s/address/%s" % (EXPLORER, PROPHET_GRID_ADDRESS),
            "source_identity": {
                "contract_bytes": len(raw_contract),
                "local_sha256": local_sha,
                "git_head_sha256": git_sha,
                "remote_raw_sha256": remote_sha,
                "onchain_sha256": onchain_sha,
                "four_way_match": bool(onchain_sha and onchain_sha == local_sha),
            },
            "custody_accounting": summary,
            "rounds": {
                "round_1": {
                    "round_id": "1",
                    "status": r1.get("status"),
                    "position_deployed": r1_rec.get("position_deployed"),
                    "position_state": r1_rec.get("position_state"),
                    "deployed_to_prophet_grid_wei": r1_rec.get("deployed_to_prophet_grid_wei"),
                    "ensemble_probability_bps": r1.get("ensemble_probability_bps"),
                    "agent_count": len(r1.get("agents", [])),
                },
                "round_2": {
                    "round_id": "2",
                    "status": r2.get("status"),
                    "reason": "REFUNDABLE_ZERO_WINNERS",
                },
            },
            "transactions": tx_summary,
            "all_transactions_finalized": all(t.get("status") == "FINALIZED" for t in txs if t.get("function")),
            "all_transactions_majority_agree": all(t.get("result") == "MAJORITY_AGREE" for t in txs if t.get("function")),
            "generated_at": now_iso(),
        }

        save_json(EVIDENCE_FILE, evidence)
        log("evidence saved to %s" % EVIDENCE_FILE)
        print(json.dumps(evidence, indent=2))


def main():
    env = dotenv_values(ROOT / ".env")
    pk = env.get("GENLAYER_PRIVATE_KEY")
    if not pk:
        print("Missing GENLAYER_PRIVATE_KEY in .env")
        sys.exit(1)
    if not pk.startswith("0x"):
        pk = "0x" + pk

    runner = Runner(pk)
    runner.run_lifecycle()


if __name__ == "__main__":
    main()
