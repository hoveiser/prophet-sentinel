# Verification and release blockers

Status: **NOT READY FOR DEPLOYMENT OR SUBMISSION**. Contract-adversarial and pre-submission checklists were applied to the local implementation. They did not pass all required gates.

## Command-backed checks
| Check | Command run | Observed result | Gate |
| --- | --- | --- | --- |
| Pinned runner and SDK semantics | `HOME="$PWD" GENVM_VERSION=v0.2.12 .venv/bin/genvm-lint check contracts/prophet_sentinel.py` | Lint passed, validation passed; 20 public methods | PASS |
| Byte limit, LF, ignored environment, working-tree secret patterns | `.venv/bin/python scripts/check_project.py` | 37,412 bytes; pinned header; LF; no detected secret patterns or public em dashes | PASS |
| Direct contract suite | `.venv/bin/pytest -q --tb=short` | 97 passed, 1 failed: donation blocks PGT confirmation | FAIL |
| Frontend calibration | `node --test frontend/tests/calibration.test.mjs` | 4 passed, including all 10,001 binary probabilities | PASS |
| Frontend build | `npm --prefix frontend run build` | Type checking and production bundle passed; large-bundle warning | PASS |
| Local browser flows | `TMPDIR="$PWD/.cache/tmp" frontend/node_modules/.bin/playwright test --config=frontend/playwright.config.ts` | 4 passed; desktop/mobile, local calibration, burner, disabled unconfigured writes | PASS |
| Local crest | `.venv/bin/python scripts/render_sentinel_crest.py` | Two 512x512 PNG copies, 55,203 bytes each | PASS |
| Local preview video | `.venv/bin/python scripts/assemble_sentinel_broadcast.py` | 50 seconds, 1280x720, 866,957 bytes; burned-in subtitles and original ambient audio | PASS |
| Canonical network and linked source | `.venv/bin/python scripts/preflight.py` | Canonical Studionet HTTP 200, chain ID 61999; deployed Grid source matches published source | PASS |
| Original RPC | Same preflight command | Original endpoint HTTP 403; not used for deployment | FAIL |
| Sentinel live lifecycle and validator agreement | Not run | No Sentinel deployment or funded live transactions | FAIL |
| Four-way Sentinel source identity | Not run | No committed/deployed/published Sentinel source identity | FAIL |
| Published CI, tag, Pages HTTP 200 | Not run | Repository publication withheld | FAIL |

The working-tree pattern check is not a full security audit or a history scan. No commits were created during this implementation. The generic workflow security notice does not point to event-field interpolation in this workflow: no GitHub event payload is inserted into shell commands, checkout credentials are not persisted, and the workspace variable is quoted. CI has not run remotely.

## Adversarial findings

### OPEN: PGT donation can freeze shared confirmation
**Severity: high, liveness / denial of service.** `confirm_pgt_withdrawal` requires the current shared PGT balance to equal the pre-withdrawal balance minus the amount. An unrelated donor can add one base unit after the real transfer. The comparison then fails, leaving `external_operation` occupied and blocking subsequent cross-contract operations.

Reproduction is the unskipped failing test `test_unsolicited_pgt_donation_cannot_block_withdrawal_confirmation`. It completes an alpha lifecycle, executes a PGT withdrawal, simulates one unsolicited PGT base unit, and expects confirmation to remain usable. Current code rejects it.

Simply replacing equality with an inequality does not establish that the intended transfer completed. Recipient balance increases can also be spoofed by donations, while spending can erase increases. Do not hide this regression or add a privileged reset.

The decoded deployed ProphetGrid source exposes `transfer_tokens`, market resolution receipts, and portfolio balances, but no per-transfer receipt method. Its source matches the published implementation. The Studionet RPC does expose transaction details through `eth_getTransactionByHash`, but using those details as contract authority requires a new exact-consensus receipt verifier with sender/target/calldata binding, replay protection, finalization checks, and independent validation. That verifier and its trust boundary are not implemented or live-tested here. No change to ProphetGrid was made.

### OPEN: terminal asynchronous child failures lack bounded recovery
Acquisition, PGT claim, and PGT withdrawal use finalized outbound messages and prohibit unsafe retries. If a child transaction permanently fails rather than soft-failing into the expected Grid ledger, the contract cannot currently prove that terminal failure and safely clear the pending operation. `test_pending_position_blocks_timeout_refund` confirms that unresolved exposure blocks refund, as required by the settlement guard, but does not prove eventual liveness.

A timeout alone is insufficient evidence that an emitted message will never execute. A verified terminal-receipt reconciliation design is needed. Native transfer delivery to actual EOAs, and behavior for non-EOA callers, also require live proof before deposits are accepted.

### OPEN: live consensus and external-source behavior
Direct tests mock web/LLM responses. They exercise the captured exact validator function with a mismatched stake, but this is not network validator agreement. Prompt injection coverage is a controlled mocked classification, not proof that an LLM reliably detects injection. Source redirects, renderer egress restrictions, unavailable evidence, and exact-comparison convergence need live verification.

### FIXED locally: nonfinal reads could settle appealable state
Every Grid read now explicitly uses `StorageType.LATEST_FINAL`. The external test double rejects any other storage mode. This avoids treating an accepted but appealable position or resolution as final. No live proof is claimed.

### FIXED locally: emission was conflated with deployment confirmation
Acquisition first records `EXECUTION_PENDING`; only observed finalized shares set `position_deployed`. Confirmation can complete before market resolution. Covered by `test_emission_does_not_mark_position_deployed`, `test_delayed_child_does_not_confirm_deployment`, and `test_confirm_deployment_before_market_resolution`.

### FIXED locally: unbacked native credit from PGT returns
Returns, bonuses, and shortfalls are explicitly PGT base units. The native ledger is not increased on PGT reconciliation. Covered by `test_native_rewards_never_count_pgt_as_native`, the full alpha lifecycle, losing-position reconciliation, and rejected-acquisition recovery.

### FIXED locally: payable and parsing edge cases
Full invalid-payment credits, partial/native withdrawals, overpayment reasons, strict probability types, approved source hosts, time bounds, malformed payable timestamps, duplicate JSON keys, and oversized model output have direct tests. The pinned SDK rejects a public `__receive__` fallback; do not send bare native transfers or assume malformed pre-dispatch calldata reaches a payable handler.

### FIXED locally: free unfunded creation reserved a market
A market is reserved only on successful funding. Competing unfunded rounds cannot lock each other out, and a losing funding attempt is fully credited. Tested by `test_unfunded_round_does_not_reserve_market`. View pagination is bounded without materializing the entire round list.

## State and race coverage
The state table is in the README. Registration is strictly before lock; audit starts at lock. Challenges are strictly before the dispute deadline; auditing is allowed through the bounded grace period; settlement is strictly after it. Timeout refunds are strictly after the timeout. Settled/refunded states reject repeat transitions. Queued external transfers are never automatically re-emitted.

Native custody equals refundable credits plus locked liabilities plus reserve in tested scenarios. Observed native balances are simulated by the direct fixture. PGT transfer confirmation and failed-child liveness remain the exceptions that prevent a safety pass.

## Submission checks still open
- No historical reviewer messages were supplied beyond the requirements in the brief. Those requirements were used as acceptance criteria; no claim of addressing unseen feedback is made.
- The original brief does not separately define Rule 7. No undocumented requirement has been invented.
- A configured live deployment's initial RPC budget, real MetaMask payments, multiple signing accounts, live early/late boundaries, explorer-verified transaction results, and native/PGT balance movement remain unverified.
- No deployment transaction, Sentinel contract address, deployed commit, `studionet-v1` tag, GitHub Pages site, or four-way source identity exists for this implementation.
- The current video is explicitly a local preview, not a completed on-chain demonstration.

The release gate remains closed. Do not generate a success-only submission block from this build.
