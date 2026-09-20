import type { RuleStatus } from "@/types";

/** One clearly different look per status, so draft can never be mistaken for confirmed. */
export default function StatusBadge({ status }: { status: RuleStatus | string }) {
  return <span className={`badge status-${status}`}>{status.toUpperCase()}</span>;
}
