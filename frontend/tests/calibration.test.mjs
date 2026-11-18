import test from "node:test";
import assert from "node:assert/strict";
import {
  brierAccuracy,
  calibrationBand,
  routingPercent,
  BANDS,
} from "../src/calibration.ts";

test("all binary probabilities use exact rational quantization", () => {
  for (let probability = 0; probability <= 10000; probability++) {
    for (const yes of [false, true]) {
      const d = BigInt(probability - (yes ? 10000 : 0));
      assert.equal(
        brierAccuracy(probability, yes),
        Number((100000000n - d * d) / 2500000n) * 250,
      );
      assert.equal(brierAccuracy(probability, yes) % 250, 0);
    }
  }
});
test("reward bands enforce exact boundary values", () => {
  assert.equal(calibrationBand(8500, 8000, false), BANDS[0]);
  assert.equal(calibrationBand(8250, 8000, false), BANDS[1]);
  assert.equal(calibrationBand(7000, 6000, false), BANDS[1]);
  assert.equal(calibrationBand(9000, 5750, false), BANDS[2]);
  assert.equal(calibrationBand(10000, 10000, true), BANDS[3]);
});
test("routing uses authenticity and dispersion, never realized outcome", () => {
  assert.equal(routingPercent(8500, 2000, false), 100);
  assert.equal(routingPercent(8250, 2000, false), 50);
  assert.equal(routingPercent(7000, 4000, false), 50);
  assert.equal(routingPercent(9000, 4001, false), 0);
  assert.equal(routingPercent(9000, 0, true), 0);
});
test("invalid probabilities are rejected", () => {
  for (const value of [-1, 10001, 1.5, NaN])
    assert.throws(() => brierAccuracy(value, true));
});
