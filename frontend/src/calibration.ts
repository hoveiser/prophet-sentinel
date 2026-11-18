export const BANDS = [
  "SUPERFORECASTER_ALPHA_YIELD",
  "CALIBRATED_CONSENSUS_PASS",
  "DRIFT_QUARANTINE_WARN",
  "HALLUCINATED_SOURCE_SLASH",
] as const;
export function brierAccuracy(probability: number, yes: boolean): number {
  if (!Number.isInteger(probability) || probability < 0 || probability > 10000)
    throw new Error("Probability out of range");
  const delta = BigInt(probability - (yes ? 10000 : 0));
  return Number((100000000n - delta * delta) / 2500000n) * 250;
}
export function calibrationBand(
  source: number,
  score: number,
  fabricated: boolean,
) {
  if (fabricated) return BANDS[3];
  if (source >= 8500 && score >= 8000) return BANDS[0];
  if (source >= 7000 && score >= 6000) return BANDS[1];
  return BANDS[2];
}
export function routingPercent(
  source: number,
  dispersion: number,
  fabricated: boolean,
) {
  if (fabricated) return 0;
  return source >= 8500 && dispersion <= 2000
    ? 100
    : source >= 7000 && dispersion <= 4000
      ? 50
      : 0;
}
