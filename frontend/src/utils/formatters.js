export function formatDate(dateStr) {
  if (!dateStr) return null;
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function formatCurrency(amount) {
  if (amount == null) return null;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: amount >= 1_000_000 ? "compact" : "standard",
    maximumFractionDigits: amount >= 1_000_000 ? 1 : 0,
  }).format(amount);
}

// Deadline urgency indicators: cards and the drawer both need urgency level and a human-readable strip label.
// Extend the existing return shape with `urgency` tier and `stripLabel`; callers that only read `label`/`color` are unaffected.
export function deadlineStatus(deadlineStr) {
  if (!deadlineStr) return null;
  const now = new Date();
  const deadline = new Date(deadlineStr);
  const diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { label: "Closed",          color: "text-red-600",              urgency: "closed",     stripLabel: "Closed" };
  if (diffDays <= 3) return { label: `${diffDays}d left`, color: "text-red-500 font-semibold",  urgency: "critical",   stripLabel: `Closes in ${diffDays}d` };
  if (diffDays <= 7) return { label: `${diffDays}d left`, color: "text-orange-500 font-semibold", urgency: "soon",     stripLabel: `Closes in ${diffDays}d` };
  if (diffDays <= 14) return { label: `${diffDays}d left`, color: "text-yellow-600",            urgency: "approaching", stripLabel: `Closes in ${diffDays}d` };
  return { label: `${diffDays}d left`, color: "text-gray-500", urgency: "normal", stripLabel: null };
}

export function buildQueryString(params) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== "" && v !== null && v !== undefined) q.set(k, v);
  });
  return q.toString();
}
