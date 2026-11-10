export function safeSourceUrl(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  try {
    const parsed = new URL(value);
    return ['https:', 'http:'].includes(parsed.protocol) ? parsed.href : undefined;
  } catch {
    return undefined;
  }
}

export function safeDownloadUrl(value: string): string | undefined {
  return /^\/api\/artifacts\/[a-zA-Z0-9_-]+\/download(?:\?[^#]*)?$/.test(value) ? value : undefined;
}
