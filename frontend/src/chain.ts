import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import type { Address } from "viem";

export const GRID = "0x31C53838fF49168128D772625e34d3D2F7e11116" as Address;
export const EXPLORER = "https://explorer-studio.genlayer.com/address/";
export const RPC = "https://studio.genlayer.com/api";
const configured =
  import.meta.env.VITE_SENTINEL_ADDRESS ||
  "0x3BD364D41fCa43c4a3D533eCb445C58316Cf4e17";
export const SENTINEL: Address | undefined = /^0x[0-9a-fA-F]{40}$/.test(
  configured,
)
  ? (configured as Address)
  : undefined;
export const reader = createClient({ chain: studionet, endpoint: RPC });
export type Client = typeof reader;
type Provider = NonNullable<Parameters<typeof createClient>[0]>["provider"];
declare global {
  interface Window {
    ethereum?: Provider;
  }
}
export type Agent = {
  address: string;
  probability_bps: number;
  source_bps: number;
  fabricated: boolean;
  url: string;
  calibration_band: string;
  quantized_brier_accuracy_bps: number;
  derived_alpha_reward: string;
  challenge: { state: string } | null;
};
export type Round = {
  round_id: string;
  market_id: string;
  status: string;
  agents: Agent[];
  ensemble_probability_bps: number;
  quantized_source_authenticity_bps: number;
  quantized_brier_accuracy_bps: number | null;
  forecast_lock_epoch: number;
  dispute_window_deadline_epoch: number;
  position_state: string;
  derived_signal_stake_wei: string;
  position_deployed: boolean;
  position_reconciled: boolean;
  pgt_return_base_units: string;
};
export type Observatory = {
  rounds: Round[];
  round_count: number;
  custody: Record<string, string | boolean>;
};
export function decode<T>(data: unknown): T {
  return (typeof data === "string" ? JSON.parse(data) : data) as T;
}
export function printable(data: unknown) {
  return JSON.stringify(
    data,
    (_, v) => (typeof v === "bigint" ? v.toString() : v),
    2,
  );
}
export async function loadObservatory(): Promise<Observatory> {
  if (!SENTINEL)
    throw new Error(
      "No verified Sentinel deployment configured. Live actions are disabled.",
    );
  return decode(
    await reader.readContract({
      address: SENTINEL,
      functionName: "get_observatory",
      args: [0, 20],
    }),
  );
}
export async function connectMetaMask() {
  const provider = window.ethereum;
  if (!provider) throw new Error("Install MetaMask to connect a wallet.");
  const accounts = (await provider.request({
    method: "eth_requestAccounts",
  })) as Address[];
  if (!accounts[0]) throw new Error("No account selected.");
  const chainId = await provider.request({ method: "eth_chainId" });
  if (chainId !== "0xf22f") {
    await provider.request({
      method: "wallet_addEthereumChain",
      params: [
        {
          chainId: "0xf22f",
          chainName: "GenLayer Studionet",
          nativeCurrency: { name: "GEN", symbol: "GEN", decimals: 18 },
          rpcUrls: [RPC],
          blockExplorerUrls: ["https://explorer-studio.genlayer.com"],
        },
      ],
    });
    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: "0xf22f" }],
    });
  }
  return {
    address: accounts[0],
    client: createClient({
      chain: studionet,
      endpoint: RPC,
      account: accounts[0],
      provider,
    }),
  };
}
export function createBurner() {
  const account = createAccount();
  return {
    address: account.address,
    client: createClient({ chain: studionet, endpoint: RPC, account }),
  };
}
