export const RECEIVER_IDENTITY_PATTERN = /^0x[0-9a-f]{64}$/i;

function normalizedReference(value: string): string {
  return RECEIVER_IDENTITY_PATTERN.test(value) ? value.toLowerCase() : value;
}

export function normalizedReceiverIdentity(value?: string | null): string | null {
  if (!value || !RECEIVER_IDENTITY_PATTERN.test(value)) return null;
  return value.toLowerCase();
}

export function receiverIdentity(
  receiver?: { receiver_identity?: string | null } | null,
): string | null {
  return normalizedReceiverIdentity(receiver?.receiver_identity);
}

export function receiverReferenceIds(
  operationalKey: string,
  receiverIdentity: string | null,
  runtimeReceiverId?: string,
): string[] {
  if (receiverIdentity) return [normalizedReference(receiverIdentity)];
  return [...new Set(
    [operationalKey, runtimeReceiverId]
      .filter((value): value is string => Boolean(value))
      .map(normalizedReference),
  )];
}

export function receiverReferencesInclude(
  references: Iterable<string>,
  receiverId: string,
): boolean {
  const candidate = normalizedReference(receiverId);
  return [...references].some((reference) => normalizedReference(reference) === candidate);
}
