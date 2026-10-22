/**
 * @param {{ stripe_test_mode?: boolean } | null | undefined} config
 * @returns {boolean}
 */
export function shouldShowStripeTestModeBanner(config) {
  return config?.stripe_test_mode === true;
}
