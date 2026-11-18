import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { formatEther, parseEther } from "viem";
import {
  GRID,
  EXPLORER,
  SENTINEL,
  reader,
  createBurner,
  connectMetaMask,
  loadObservatory,
  decode,
  printable,
  type Client,
  type Observatory,
  type Round,
} from "./chain";
import {
  BANDS,
  brierAccuracy,
  calibrationBand,
  routingPercent,
} from "./calibration";
import "./style.css";

const short = (s: string) => s.slice(0, 6) + "..." + s.slice(-4);
const amount = (s: unknown) => {
  try {
    return formatEther(BigInt(String(s ?? "0")));
  } catch {
    return "?";
  }
};
const pct = (n: number) => (n / 100).toFixed(2) + "%";
const bandName = (s: string) => s.replaceAll("_", " ");
const steps = [
  ["01", "Observe", "Primary-source citations"],
  ["02", "Converge", "Source-based signal routing"],
  ["03", "Reconcile", "Real ProphetGrid positions"],
  ["04", "Calibrate", "Realized Brier accuracy"],
];
const actions: Record<string, string> = {
  audit_forecaster_swarm: "Audit primary sources",
  execute_signal_position_on_prophet_grid: "Execute signal position",
  reconcile_prophet_grid_outcome: "Reconcile ProphetGrid",
  finalize_realized_calibration: "Compute realized calibration",
  settle_forecaster_round: "Settle forecaster round",
  claim_unverified_round_refund: "Recover unverified round",
};

function Workbench() {
  const [p, setP] = useState(7800),
    [second, setSecond] = useState(8400),
    [source, setSource] = useState(9000);
  const [yes, setYes] = useState(true),
    [fabricated, setFabricated] = useState(false);
  const mean = Math.floor((p + second) / 2),
    score = brierAccuracy(mean, yes),
    band = calibrationBand(source, score, fabricated);
  const points = Array.from(
    { length: 101 },
    (_, i) => `${50 + i * 5.2},${230 - brierAccuracy(i * 100, yes) / 50}`,
  ).join(" ");
  return (
    <section id="calibration" className="panel workbench">
      <div className="panel-head">
        <div>
          <span className="eyebrow">02 / CALIBRATION WORKBENCH</span>
          <h2>Confidence meets consequence.</h2>
        </div>
        <span className="chip violet">LOCAL MODEL</span>
      </div>
      <p className="muted">
        Explore exact thresholds. These inputs are illustrative, not validator
        findings or live forecasts.
      </p>
      <div className="workbench-grid">
        <div className="chart-wrap">
          <div className="chart-caption">
            <span>QUANTIZED BRIER ACCURACY</span>
            <span>250 BPS GRID</span>
          </div>
          <svg
            viewBox="0 0 630 285"
            role="img"
            aria-label="Brier accuracy curve for the selected hypothetical outcome"
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <g key={i}>
                <line
                  x1="50"
                  x2="570"
                  y1={30 + i * 50}
                  y2={30 + i * 50}
                  stroke="#2b263b"
                  strokeDasharray="3 6"
                />
                <text x="5" y={35 + i * 50}>
                  {100 - i * 25}%
                </text>
              </g>
            ))}
            <polyline
              points={points}
              fill="none"
              stroke="#8b5cf6"
              strokeWidth="3"
            />
            <line
              x1={50 + mean * 0.052}
              x2={50 + mean * 0.052}
              y1="25"
              y2="230"
              stroke="#f59e0b"
              strokeDasharray="4 5"
            />
            <circle
              cx={50 + mean * 0.052}
              cy={230 - score / 50}
              r="7"
              fill="#f59e0b"
              stroke="#ffe1a0"
              strokeWidth="2"
            />
            {[0, 25, 50, 75, 100].map((n) => (
              <text key={n} x={45 + n * 5.2} y="255">
                {n}%
              </text>
            ))}
            <text x="220" y="280">
              ENSEMBLE PROBABILITY / YES
            </text>
          </svg>
          <div className="chart-values">
            <div>
              <small>Ensemble</small>
              <strong>{pct(mean)}</strong>
            </div>
            <div>
              <small>Realized accuracy</small>
              <strong className="amber">{pct(score)}</strong>
            </div>
            <div>
              <small>Signal allocation</small>
              <strong>
                {routingPercent(source, Math.abs(p - second), fabricated)}%
              </strong>
            </div>
          </div>
          <p className="fine">
            Allocation uses source authenticity and dispersion only. The
            hypothetical outcome affects Brier scoring, never pre-close routing.
          </p>
        </div>
        <div className="sliders">
          {[
            ["Agent A probability", p, setP, 100],
            ["Agent B probability", second, setSecond, 100],
            ["Source authenticity", source, setSource, 250],
          ].map(([label, val, setter, step]) => (
            <label key={String(label)}>
              <span>
                {String(label)}
                <b>{pct(Number(val))}</b>
              </span>
              <input
                type="range"
                min="0"
                max="10000"
                step={Number(step)}
                value={Number(val)}
                onChange={(e) =>
                  (setter as (n: number) => void)(Number(e.target.value))
                }
              />
            </label>
          ))}
          <label>
            <span>Hypothetical resolved outcome</span>
            <select
              value={yes ? "YES" : "NO"}
              onChange={(e) => setYes(e.target.value === "YES")}
            >
              <option>YES</option>
              <option>NO</option>
            </select>
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={fabricated}
              onChange={(e) => setFabricated(e.target.checked)}
            />{" "}
            Model proven fabrication
          </label>
          <div className={"band-result band-" + BANDS.indexOf(band)}>
            <small>POST-RESOLUTION BAND</small>
            <strong>{bandName(band)}</strong>
          </div>
        </div>
      </div>
      <div className="bands">
        {BANDS.map((b, i) => (
          <div key={b} className={band === b ? "selected" : ""}>
            <span className={"band-dot dot-" + i} />
            <strong>
              {
                [
                  "Superforecaster",
                  "Calibrated pass",
                  "Drift quarantine",
                  "Source fabrication",
                ][i]
              }
            </strong>
            <small>
              {
                [
                  "100% bounty + bond",
                  "60% bounty + bond",
                  "Bond returned",
                  "Proven offender bond slashed",
                ][i]
              }
            </small>
          </div>
        ))}
      </div>
    </section>
  );
}

function App() {
  const [data, setData] = useState<Observatory>(),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  const [wallet, setWallet] = useState<{ address: string; client: Client }>(),
    [walletNote, setWalletNote] = useState("");
  const [selected, setSelected] = useState(""),
    [operation, setOperation] = useState("audit_forecaster_swarm");
  const [busy, setBusy] = useState(false),
    [tx, setTx] = useState(""),
    [receipt, setReceipt] = useState("");
  const [accountLedger, setAccountLedger] = useState<Record<string, string>>(),
    [showOperator, setShowOperator] = useState(false);
  const [now, setNow] = useState(Date.now()),
    [details, setDetails] = useState("");
  async function refresh() {
    setLoading(true);
    setError("");
    try {
      setData(await loadObservatory());
    } catch (e) {
      setError(e instanceof Error ? e.message : "RPC unavailable");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    const provider = window.ethereum as
      | {
          on?: (event: string, handler: () => void) => void;
          removeListener?: (event: string, handler: () => void) => void;
        }
      | undefined;
    const reset = () => {
      setWallet(undefined);
      setAccountLedger(undefined);
      setWalletNote("Wallet context changed. Reconnect before signing.");
    };
    provider?.on?.("accountsChanged", reset);
    provider?.on?.("chainChanged", reset);
    return () => {
      provider?.removeListener?.("accountsChanged", reset);
      provider?.removeListener?.("chainChanged", reset);
    };
  }, []);
  const current: Round | undefined = data?.rounds.find(
    (r) => r.round_id === selected,
  );
  const countdown = (epoch: number) =>
    epoch
      ? Math.max(0, Math.floor(epoch - now / 1000)) + "s"
      : "Awaiting resolution";
  async function metaMask() {
    try {
      setWallet(await connectMetaMask());
      setWalletNote(
        "MetaMask connected. Verify every transaction before signing.",
      );
    } catch {
      setWalletNote(
        "Wallet connection failed or was declined. Check MetaMask and the selected network.",
      );
    }
  }
  async function ledger() {
    if (!wallet || !SENTINEL) return;
    try {
      setAccountLedger(
        decode(
          await reader.readContract({
            address: SENTINEL,
            functionName: "get_refundable_balance",
            args: [wallet.address],
          }),
        ),
      );
    } catch {
      setError("Could not read the wallet refund ledger.");
    }
  }
  async function send(
    method: string,
    args: (string | number | bigint)[],
    value = 0n,
  ) {
    if (!wallet || !SENTINEL || busy) return;
    setBusy(true);
    setError("");
    setReceipt("");
    try {
      const hash = await wallet.client.writeContract({
        address: SENTINEL,
        functionName: method,
        args,
        value,
      });
      setTx(String(hash));
      setReceipt(
        "Submitted. Finalization, execution result, and resulting state still need verification. Do not resubmit while pending.",
      );
    } catch {
      setError(
        "Submission was rejected or its outcome is unknown. Inspect wallet history before retrying.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function inspectReceipt() {
    if (!/^0x[0-9a-fA-F]{64}$/.test(tx)) return;
    try {
      setReceipt(
        printable(
          await reader.getTransaction({
            hash: tx as Parameters<typeof reader.getTransaction>[0]["hash"],
          }),
        ),
      );
      await refresh();
      await ledger();
    } catch {
      setError("Receipt is unavailable. This does not prove execution failed.");
    }
  }
  async function inspectRound() {
    if (!SENTINEL || !selected) return;
    try {
      setDetails(
        printable(
          await reader.readContract({
            address: SENTINEL,
            functionName: "get_round_prophet_grid_reconciliation",
            args: [selected],
          }),
        ),
      );
    } catch {
      setError("Reconciliation state is unavailable.");
    }
  }
  function formSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget),
      type = String(f.get("type"));
    try {
      if (type === "create")
        void send("create_forecaster_round", [
          String(f.get("market")),
          Number(f.get("forecast")),
          Number(f.get("dispute")),
          parseEther(String(f.get("bond"))),
        ]);
      if (type === "fund")
        void send(
          "fund_signal_bounty_payable",
          [String(f.get("round")), parseEther(String(f.get("budget")))],
          parseEther(String(f.get("total"))),
        );
      if (type === "register")
        void send(
          "register_forecaster_signal_payable",
          [
            String(f.get("round")),
            Number(f.get("probability")),
            String(f.get("citation")),
          ],
          parseEther(String(f.get("bond"))),
        );
      if (type === "challenge")
        void send(
          "challenge_fabricated_citation_payable",
          [
            String(f.get("round")),
            String(f.get("agent")),
            String(f.get("citation")),
          ],
          parseEther(String(f.get("bond"))),
        );
      if (type === "audit")
        void send("audit_citation_challenge", [
          String(f.get("round")),
          String(f.get("agent")),
        ]);
    } catch {
      setError("Invalid amount or input. No transaction was submitted.");
    }
  }
  const canWrite = !!wallet && !!SENTINEL && !busy;
  return (
    <>
      <div className="orbital-grid" />
      <header>
        <a className="brand" href="#">
          <img
            src={import.meta.env.BASE_URL + "logo.png"}
            alt="ProphetSentinel crest"
          />
          <span>
            PROPHET<span className="amber">SENTINEL</span>
            <small>FORECAST INTELLIGENCE NETWORK</small>
          </span>
        </a>
        <nav>
          <a href="#swarm">Swarm matrix</a>
          <a href="#calibration">Calibration</a>
          <a href="#evidence">Dispute radar</a>
        </nav>
        <button className="wallet" onClick={metaMask}>
          {wallet ? short(wallet.address) : "Connect MetaMask"} <span>↗</span>
        </button>
      </header>
      <main>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="pulse" /> PROPHETGRID ECOSYSTEM / MODULE 02
            </div>
            <h1>
              Many forecasts.
              <br />
              <span>One accountable signal.</span>
            </h1>
            <p>
              Primary-source evidence in. Calibrated intelligence out.
              <br />
              An observatory for agents that put conviction on the line.
            </p>
            <div className="hero-actions">
              <a className="button primary" href="#swarm">
                Enter the observatory <span>↓</span>
              </a>
              <a
                className="text-link"
                href={EXPLORER + GRID}
                target="_blank"
                rel="noreferrer"
              >
                Inspect ProphetGrid ↗
              </a>
            </div>
            <div className="hero-meta">
              <span>EXACT CONSENSUS</span>
              <i />
              <span>250 BPS PRECISION</span>
              <i />
              <span>ASSET-SEPARATE CUSTODY</span>
            </div>
          </div>
          <div className="radar" aria-hidden="true">
            <div className="radar-ring r1" />
            <div className="radar-ring r2" />
            <div className="radar-ring r3" />
            <div className="radar-cross h" />
            <div className="radar-cross v" />
            <div className="radar-sweep" />
            <div className="radar-core">
              P<span>S</span>
            </div>
            <span className="radar-node n1" />
            <span className="radar-node n2" />
            <span className="radar-node n3" />
            <span className="radar-label l1">SOURCE / VERIFY</span>
            <span className="radar-label l2">SIGNAL / CONVERGE</span>
            <span className="radar-caption">ILLUSTRATIVE NETWORK TOPOLOGY</span>
          </div>
        </section>
        <div className="network-strip">
          <span className={"status-dot " + (data ? "green" : "")} />
          <strong>
            {loading
              ? "READING NETWORK"
              : data
                ? "CONTRACT SNAPSHOT LOADED"
                : "DEPLOYMENT NOT VERIFIED"}
          </strong>
          <span>Studionet · 61999</span>
          <span className="strip-end">PGT ≠ NATIVE GEN</span>
        </div>
        <div className="pipeline">
          {steps.map(([n, title, label]) => (
            <div key={n}>
              <span>{n}</span>
              <div>
                <strong>{title}</strong>
                <small>{label}</small>
              </div>
              <b>↗</b>
            </div>
          ))}
        </div>
        {error && (
          <div className="notice" role="status">
            <span>NOTICE</span>
            {error}
          </div>
        )}
        <section id="swarm" className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">01 / MULTI-AGENT SWARM MATRIX</span>
              <h2>Follow the signal. Inspect the stake.</h2>
            </div>
            <div className="actions">
              <button onClick={refresh} disabled={loading}>
                ↻ Refresh
              </button>
              <button
                className="primary"
                onClick={() => setShowOperator(!showOperator)}
              >
                Agent operator +
              </button>
            </div>
          </div>
          <div className="metrics">
            <div>
              <small>Forecast rounds</small>
              <strong>{data?.round_count ?? "--"}</strong>
              <span>On-chain registered rounds</span>
            </div>
            <div>
              <small>Native vault custody</small>
              <strong>
                {data ? amount(data.custody.vault_custody_balance_wei) : "--"}{" "}
                <em>GEN</em>
              </strong>
              <span>Independent forecaster collateral</span>
            </div>
            <div>
              <small>Reconciled return credits</small>
              <strong>
                {data ? amount(data.custody.pgt_credit_base_units) : "--"}{" "}
                <em>PGT</em>
              </strong>
              <span>Not native-GEN redemption</span>
            </div>
            <div>
              <small>Custody invariant</small>
              <strong
                className={
                  data?.custody.native_invariant_ok && data?.custody.native_backing_ok ? "emerald" : "muted"
                }
              >
                {data
                  ? data.custody.native_invariant_ok && data.custody.native_backing_ok
                    ? "BALANCED"
                    : "FAILED"
                  : "UNVERIFIED"}
              </strong>
              <span>Credits + locked funds + reserve</span>
            </div>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ROUND / MARKET</th>
                  <th>ENSEMBLE YES</th>
                  <th>SOURCE AUTHENTICITY</th>
                  <th>GRID POSITION</th>
                  <th>REALIZED BRIER</th>
                </tr>
              </thead>
              <tbody>
                {data?.rounds.map((r) => (
                  <tr
                    key={r.round_id}
                    onClick={() => setSelected(r.round_id)}
                    className={selected === r.round_id ? "active-row" : ""}
                  >
                    <td>
                      <button
                        className="row-button"
                        onClick={() => setSelected(r.round_id)}
                      >
                        Round {r.round_id}{" "}
                        <small>ProphetGrid #{r.market_id}</small>
                      </button>
                    </td>
                    <td>
                      <b className="amber">{pct(r.ensemble_probability_bps)}</b>
                      <div className="meter">
                        <i style={{ width: pct(r.ensemble_probability_bps) }} />
                      </div>
                    </td>
                    <td>{pct(r.quantized_source_authenticity_bps)}</td>
                    <td>
                      <span className="chip">{r.position_state}</span>
                    </td>
                    <td>
                      {r.quantized_brier_accuracy_bps === null
                        ? "AWAITING OUTCOME"
                        : pct(r.quantized_brier_accuracy_bps)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!data?.rounds.length && (
            <div className="empty">
              <div className="empty-reticle">◎</div>
              <h3>
                {data
                  ? "The swarm has not assembled yet."
                  : "Awaiting a verified deployment."}
              </h3>
              <p>
                {data
                  ? "Create a round linked to an open ProphetGrid market to begin."
                  : "No invented agents, balances, positions, or transaction evidence. Explore the calibration model below."}
              </p>
            </div>
          )}
          {current && (
            <div className="agent-list">
              {current.agents.map((a) => (
                <div key={a.address}>
                  <strong>{short(a.address)}</strong>
                  <span>{pct(a.probability_bps)} YES</span>
                  <a href={a.url} target="_blank" rel="noreferrer">
                    Primary citation ↗
                  </a>
                  <span className="chip">{bandName(a.calibration_band)}</span>
                </div>
              ))}
            </div>
          )}
        </section>
        {showOperator && (
          <section className="panel operator">
            <div className="panel-head">
              <div>
                <span className="eyebrow">AGENT OPERATOR</span>
                <h2>Commit evidence, not just conviction.</h2>
              </div>
              <button
                onClick={() => {
                  setWallet(createBurner());
                  setWalletNote(
                    "Memory-only burner created. Refreshing or closing this page loses access. Use only disposable test funds.",
                  );
                }}
              >
                Create burner agent
              </button>
            </div>
            <p className="notice">
              {walletNote ||
                "Connect MetaMask or create a memory-only burner. Use test funds only. No private keys are stored or displayed."}
            </p>
            <div className="operator-forms">
              {["create", "fund", "register", "challenge", "audit"].map(
                (type) => (
                  <form key={type} onSubmit={formSubmit}>
                    <input name="type" type="hidden" value={type} />
                    <h3>
                      {
                        (
                          {
                            create: "Create forecasting round",
                            fund: "Fund bounty and signal",
                            register: "Register forecaster",
                            challenge: "Challenge fabricated citation",
                            audit: "Audit pending challenge",
                          } as Record<string, string>
                        )[type]
                      }
                    </h3>
                    {type === "create" ? (
                      <>
                        <label>
                          ProphetGrid market ID
                          <input
                            name="market"
                            required
                            pattern="[0-9]+"
                            placeholder="Existing open market"
                          />
                        </label>
                        <label>
                          Forecast window (seconds)
                          <input
                            name="forecast"
                            type="number"
                            min="600"
                            max="2592000"
                            defaultValue="600"
                            required
                          />
                        </label>
                        <label>
                          Dispute window (seconds)
                          <input
                            name="dispute"
                            type="number"
                            min="600"
                            max="2592000"
                            defaultValue="600"
                            required
                          />
                        </label>
                      </>
                    ) : (
                      <label>
                        Sentinel round ID
                        <input
                          name="round"
                          required
                          defaultValue={selected}
                          placeholder="Round ID"
                        />
                      </label>
                    )}
                    {["create", "register", "challenge"].includes(type) && (
                      <label>
                        Bond (GEN)
                        <input
                          name="bond"
                          defaultValue="0.000001"
                          required
                          inputMode="decimal"
                        />
                      </label>
                    )}
                    {type === "fund" && (
                      <>
                        <label>
                          Total native payment (GEN)
                          <input name="total" defaultValue="0.00001" required />
                        </label>
                        <label>
                          Dedicated signal budget (GEN)
                          <input
                            name="budget"
                            defaultValue="0.000002"
                            required
                          />
                        </label>
                        <p className="fine">
                          The remainder is the bounty. Signal principal is at
                          risk and returns as PGT, not native GEN.
                        </p>
                      </>
                    )}
                    {type === "register" && (
                      <label>
                        YES probability (basis points)
                        <input
                          name="probability"
                          type="number"
                          min="0"
                          max="10000"
                          step="1"
                          defaultValue="7500"
                          required
                        />
                      </label>
                    )}
                    {["challenge", "audit"].includes(type) && (
                      <label>
                        Agent address
                        <input
                          name="agent"
                          required
                          pattern="0x[0-9a-fA-F]{40}"
                          placeholder="0x..."
                        />
                      </label>
                    )}
                    {["register", "challenge"].includes(type) && (
                      <label>
                        Primary-source URL
                        <input
                          name="citation"
                          type="url"
                          required
                          placeholder="https://www.nasa.gov/..."
                        />
                      </label>
                    )}
                    <button disabled={!canWrite} type="submit">
                      {busy ? "Awaiting wallet..." : "Submit " + type} ↗
                    </button>
                  </form>
                ),
              )}
            </div>
          </section>
        )}
        <Workbench />
        <div className="bottom-grid">
          <section id="evidence" className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">03 / DISPUTE RADAR</span>
                <h2>Every transition leaves a trace.</h2>
              </div>
              <span className="chip violet">EVIDENCE FIRST</span>
            </div>
            <label>
              Forecast round
              <select
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
              >
                <option value="">Select an on-chain round</option>
                {data?.rounds.map((r) => (
                  <option key={r.round_id} value={r.round_id}>
                    Round {r.round_id} / Market {r.market_id}
                  </option>
                ))}
              </select>
            </label>
            <div className="timeline">
              <div>
                <span />
                <small>FORECAST LOCK</small>
                <strong>
                  {current ? countdown(current.forecast_lock_epoch) : "--"}
                </strong>
              </div>
              <div>
                <span />
                <small>DISPUTE DEADLINE</small>
                <strong>
                  {current
                    ? countdown(current.dispute_window_deadline_epoch)
                    : "--"}
                </strong>
              </div>
            </div>
            <p className="fine">
              Countdowns use browser time for display only. The contract
              enforces consensus timestamps and an additional challenge-audit
              grace period.
            </p>
            <div className="execution-form">
              <select
                aria-label="Lifecycle operation"
                value={operation}
                onChange={(e) => setOperation(e.target.value)}
              >
                {Object.entries(actions).map(([name, label]) => (
                  <option key={name} value={name}>
                    {label}
                  </option>
                ))}
              </select>
              <button
                className="primary"
                disabled={!canWrite || !selected}
                onClick={() => send(operation, [selected])}
              >
                Execute ↗
              </button>
            </div>
            <button onClick={inspectRound} disabled={!selected || !SENTINEL}>
              Read reconciliation evidence
            </button>
            {details && <pre>{details}</pre>}
            <div className="tx-box">
              <small>TRANSACTION EVIDENCE</small>
              {tx ? (
                <>
                  <code>{tx}</code>
                  <button onClick={inspectReceipt}>
                    Inspect receipt and refresh state
                  </button>
                  <pre>{receipt}</pre>
                </>
              ) : (
                <p>No transaction submitted in this session.</p>
              )}
            </div>
          </section>
          <section className="panel refund">
            <span className="eyebrow">04 / CUSTODY AND RECOVERY</span>
            <h2>
              Your assets.
              <br />
              Two separate ledgers.
            </h2>
            <p className="muted">
              Rejected payable calls credit a claim in Sentinel. ProphetGrid
              returns remain PGT, independently reconciled.
            </p>
            <div className="ledger-line">
              <span>Native GEN / PFT credit</span>
              <strong>
                {accountLedger ? amount(accountLedger.native_wei) : "--"}
              </strong>
            </div>
            <div className="ledger-line">
              <span>ProphetGrid PGT credit</span>
              <strong className="violet-text">
                {accountLedger ? amount(accountLedger.pgt_base_units) : "--"}
              </strong>
            </div>
            {accountLedger?.last_payable_rejection && (
              <p className="notice">{accountLedger.last_payable_rejection}</p>
            )}
            <button disabled={!wallet || !SENTINEL} onClick={ledger}>
              Read my refund ledger
            </button>
            <button
              className="primary full"
              disabled={
                !canWrite ||
                !accountLedger ||
                BigInt(accountLedger.native_wei) === 0n
              }
              onClick={() => send("claim_refundable_balance", [])}
            >
              Claim native refund ↗
            </button>
            <button
              className="full"
              disabled={
                !canWrite ||
                !accountLedger ||
                BigInt(accountLedger.pgt_base_units) === 0n
              }
              onClick={() =>
                send("withdraw_pgt", [BigInt(accountLedger!.pgt_base_units)])
              }
            >
              Withdraw PGT credit ↗
            </button>
            <button
              className="full"
              disabled={!canWrite}
              onClick={() => send("confirm_pgt_withdrawal", [])}
            >
              Confirm pending PGT withdrawal
            </button>
            <p className="fine">
              Submissions are not payment confirmations. Check finalized
              execution and balances before treating a transfer as received.
            </p>
          </section>
        </div>
        <footer>
          <div className="brand-text">
            PROPHET<span className="amber">SENTINEL</span>
            <small>
              Intelligence is a forecast. Accountability is on-chain.
            </small>
          </div>
          <div>
            <a href={EXPLORER + GRID} target="_blank" rel="noreferrer">
              ProphetGrid contract ↗
            </a>
            {SENTINEL && (
              <a href={EXPLORER + SENTINEL} target="_blank" rel="noreferrer">
                Sentinel contract ↗
              </a>
            )}
            <a href={import.meta.env.BASE_URL + "demo-video-subtitled.mp4"} target="_blank" rel="noreferrer">Local preview video ↗</a>
            <span>STUDIONET DEVELOPMENT BUILD</span>
          </div>
        </footer>
      </main>
    </>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
