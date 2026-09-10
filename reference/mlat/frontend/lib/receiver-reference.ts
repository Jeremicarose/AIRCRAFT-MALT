const CKB_RECEIVER_IDENTITY = /^0x[0-9a-f]{64}$/i;

function normalizedReference(value: string): string {
  return CKB_RECEIVER_IDENTITY.test(value) ? value.toLowerCase() : value;
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
