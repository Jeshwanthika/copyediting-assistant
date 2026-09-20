/** Turn a 0-1 match strength into words a trainee can understand. */
export function confidenceLabel(confidence: number): string {
  const percent = Math.round(confidence * 100);
  if (confidence >= 0.9) return `High (${percent}%)`;
  if (confidence >= 0.7) return `Medium (${percent}%)`;
  return `Low (${percent}%)`;
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** e.g. "Initial team guidance — Draft" */
export function sourceLabel(source: string, status: string | null): string {
  return status ? `${source} — ${capitalize(status)}` : source;
}
