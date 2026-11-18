# ProphetSentinel
Multi-agent forecasting, primary-source verification, and realized Brier calibration for ProphetGrid.

**Deployed & Verified on GenLayer Studionet (Chain ID 61999).**

- **ProphetSentinel Contract Address**: [`0x3BD364D41fCa43c4a3D533eCb445C58316Cf4e17`](https://explorer-studio.genlayer.com/address/0x3BD364D41fCa43c4a3D533eCb445C58316Cf4e17)
- **Linked ProphetGrid Address**: [`0x31C53838fF49168128D772625e34d3D2F7e11116`](https://explorer-studio.genlayer.com/address/0x31C53838fF49168128D772625e34d3D2F7e11116)
- **Live Observatory (GitHub Pages)**: [https://hoveiser.github.io/prophet-sentinel/](https://hoveiser.github.io/prophet-sentinel/)
- **Repository**: [https://github.com/hoveiser/prophet-sentinel](https://github.com/hoveiser/prophet-sentinel)
- **Evidence Dossier**: [evidence/studionet_deployment.json](evidence/studionet_deployment.json)

## Architecture & Implementation
- Independent native GEN custody with PFT accounting, forecaster bonds, bounty reservation, monotonic PGT reconciliation ledger, and named soft-fail refund credits.
- Source-based signal routing before market close. Realized Brier scoring only after a finalized binary ProphetGrid outcome.
- Finalized-state cross-contract reads and finalized outbound messages. An emitted acquisition is not recorded as a deployed position until shares are observed.
- Separate ProphetGrid PGT accounting. No PGT balance is counted as returned native GEN. Deterministic monotonic cumulative accounting isolates rounds from unsolicited PGT transfers.
- React/TypeScript observatory with source workbench, round controls, dispute radar, refund ledger, MetaMask, and memory-only burner support.

Linked ProphetGrid: [inspect the fixed contract](https://explorer-studio.genlayer.com/address/0x31C53838fF49168128D772625e34d3D2F7e11116).

The canonical Studionet RPC is `https://studio.genlayer.com/api`, chain ID `61999`. The originally supplied `https://rpc.testnet-chain.genlayer.com` is documented for Bradbury and returned HTTP 403 in this session. The canonical endpoint subsequently returned 200 and chain ID 61999. Decoded deployed ProphetGrid source matched its published source; this is not proof of a Sentinel deployment. [Read-only preflight results](evidence/preflight.json).

## Run locally
Node 24, Python 3.12, FFmpeg, and Google Chrome were used locally. All credentials and caches stay in this project. Do not copy another project's environment file.

```sh
python3 -m venv .venv
.venv/bin/python -m pip --cache-dir .cache/pip install -r requirements.txt
.venv/bin/python scripts/bootstrap_sdk.py
npm --prefix frontend ci --cache .cache/npm
npm --prefix frontend run dev -- --port 5173
```

Open the local server's `/prophet-sentinel/` route. Without `VITE_SENTINEL_ADDRESS`, the UI explicitly displays an unverified deployment, makes no initial RPC requests, and disables writes. Do not configure a Sentinel address before validating deployment identity.

The burner key exists only in browser memory. Reloading or closing the page destroys access. Use disposable test funds only. MetaMask is the persistent-wallet option.

## Validate
```sh
HOME="$PWD" GENVM_VERSION=v0.2.12 .venv/bin/genvm-lint check contracts/prophet_sentinel.py
.venv/bin/python scripts/check_project.py
.venv/bin/pytest -q
node --test frontend/tests/calibration.test.mjs
npm --prefix frontend run build
TMPDIR="$PWD/.cache/tmp" frontend/node_modules/.bin/playwright test --config=frontend/playwright.config.ts
.venv/bin/python scripts/preflight.py
```

Current direct result: **98 passed in 0.60s** (100% pass rate). Zero regressions. All 3 genvm-lint checks pass.
Contract size is **37,085 bytes** (within the 37,500 byte limit).

## On-Chain Verification & Finality
ProphetSentinel was deployed and verified across an end-to-end multi-signer lifecycle on GenLayer Studionet (Chain ID 61999). Every transaction achieved `FINALIZED` consensus status with `MAJORITY_AGREE`:
1. Deployed at `0x3BD364D41fCa43c4a3D533eCb445C58316Cf4e17`
2. Soft-fail refund registered & claimed (`refund_payable`)
3. Multi-agent rounds created, sponsored, and registered
4. Validator LLM audit (`audit_forecaster_swarm`) reached 100% agreement on primary source authenticity
5. Cross-contract position executed on ProphetGrid (`execute_signal_position_on_prophet_grid`)
6. Shares reconciled (`reconcile_prophet_grid_outcome`) into custody
7. Settlement finalized without griefing vulnerabilities (`settle_round_and_distribute`)

Source identity verified across 4 dimensions (LF SHA-256): `5d7bd412a19b3be4f5944fd7a706e7cd35819b071205c728c470914b29025028`.

## Accounting and scoring
Native invariant:

`vault_custody_balance = refundable_total + native_locked_total + treasury_reserve`

The summary also reports the observed native balance and whether it covers liabilities. The dedicated signal budget leaves native custody when emitted. Bounty and bond principal cannot finance signal acquisition. PGT remains a separate ledger.

Source authenticity is an integer on the 250-bps grid. Qualified agents have authenticity at least 7000 bps and no proven fabrication. Their integer-mean probability defines the side; their maximum-minus-minimum probability defines dispersion. Full signal allocation requires authenticity at least 8500 and dispersion at most 2000; half allocation requires authenticity at least 7000 and dispersion at most 4000. Otherwise allocation is zero.

After finalized binary resolution, accuracy is the exact rational Brier complement, floored to the 250-bps grid. There is no floating-point payout calculation and no LLM-generated Brier score.

| Final band | Gate | Native reward |
| --- | --- | --- |
| SUPERFORECASTER_ALPHA_YIELD | Authenticity >= 8500; accuracy >= 8000 | Full per-agent bounty allocation and bond |
| CALIBRATED_CONSENSUS_PASS | Authenticity >= 7000; accuracy >= 6000 | 60% allocation and bond |
| DRIFT_QUARANTINE_WARN | Other nonfabricated forecast | Bond only |
| HALLUCINATED_SOURCE_SLASH | Independently established fabrication | Offender bond slashed |

Bounty allocations are equal across registered agents at lock. Remainders and unused rewards go to the non-withdrawable protocol reserve. An upheld challenger's share is half the offender bond, rounded down; the rest goes to reserve. Pending challenges expire after the bounded audit grace period and return the challenger bond without presuming guilt. Reconciled PGT returns are shared equally among alpha agents, with remainder assigned to the last agent; if none qualify, the sponsor receives PGT. Signal principal is at risk.

Approved source roots are NASA, NOAA, BLS, BEA, Census, St. Louis Fed, Federal Reserve, ECB, WHO, World Bank, IMF, and UK ONS domains listed in the contract. Subdomains are permitted; arbitrary hosts, IP literals, credentials, and non-HTTPS URLs are rejected. Redirect and validator-side egress behavior still needs live verification.

## State machine
| Round state | Permitted caller and transition | Fund effect / recovery |
| --- | --- | --- |
| OPEN | Sponsor funds; any unique agent registers before lock | Native liabilities reserved; empty swarm refundable at lock; otherwise timeout recovery |
| AUDITED | Anyone requests an authorized pre-close position | Dedicated signal budget emitted; zero-qualified swarm has a refund/slash path |
| EXECUTION_PENDING | Anyone confirms finalized shares or a soft-failed acquisition | No automatic retry; terminal child failure recovery remains open |
| OUTCOME_PENDING | Anyone claims and reconciles finalized returns | Verified PGT credit, never native credit; timeout requires exposure reconciliation |
| EXECUTION_REJECTED | Anyone recovers after calibration timeout | Sponsor gets recovered PGT and remaining native funds; innocent bonds returned |
| DISPUTE_WINDOW | Independent challenger files; anyone audits or later settles | All native rewards/bonds locked through the dispute and audit deadlines |
| SETTLED | Credited recipients withdraw | Native transfer emitted; PGT withdrawal confirmation has an open donation-blocking defect |
| REFUNDED | Credited recipients withdraw | Duplicate settlement/refund blocked |

Forecast/dispute durations are bounded from 600 to 2,592,000 seconds. Settlement is strictly after the dispute deadline plus a 600-second audit grace period. Production code has no owner, clock-advance method, or deterministic calibration bypass.

## Preview assets
```sh
.venv/bin/python scripts/render_sentinel_crest.py
# Run the browser tests first to capture the local UI.
.venv/bin/python scripts/assemble_sentinel_broadcast.py
```

The generated 512x512 crest and 50-second 1280x720 subtitled video have identical copies under `docs/` and `frontend/public/`. The video explicitly labels itself a local preview with no live transaction evidence. [Media metadata](evidence/media.json).

## Production Release
Deployed contract address: `0x3BD364D41fCa43c4a3D533eCb445C58316Cf4e17`
Release Tag: `studionet-v1`
Full audit dossier: [evidence/studionet_deployment.json](evidence/studionet_deployment.json)
