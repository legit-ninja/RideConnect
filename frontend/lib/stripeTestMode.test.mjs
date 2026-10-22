import assert from "node:assert/strict";
import { test } from "node:test";

import { shouldShowStripeTestModeBanner } from "./stripeTestMode.mjs";

test("banner shown for test mode", () => {
  assert.equal(shouldShowStripeTestModeBanner({ stripe_test_mode: true }), true);
});

test("banner hidden for live mode", () => {
  assert.equal(shouldShowStripeTestModeBanner({ stripe_test_mode: false }), false);
});
