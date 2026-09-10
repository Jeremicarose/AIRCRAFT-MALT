export const RECEIVER_STALE_AFTER_SECONDS = 120;
export const RECEIVER_FUTURE_SKEW_SECONDS = 30;

export type ReceiverObservationFreshness = 'fresh' | 'stale' | 'invalid' | 'future';

export function classifyReceiverObservation(
  lastSeen: unknown,
  nowSeconds = Date.now() / 1000,
  staleAfterSeconds = RECEIVER_STALE_AFTER_SECONDS,
  futureSkewSeconds = RECEIVER_FUTURE_SKEW_SECONDS,
): ReceiverObservationFreshness {
  const observedAt = Number(lastSeen);
  if (
    !Number.isFinite(observedAt)
    || observedAt <= 0
    || !Number.isFinite(nowSeconds)
    || staleAfterSeconds < 0
    || futureSkewSeconds < 0
  ) {
    return 'invalid';
  }
  if (observedAt > nowSeconds + futureSkewSeconds) return 'future';
  if (nowSeconds - observedAt > staleAfterSeconds) return 'stale';
  return 'fresh';
}
