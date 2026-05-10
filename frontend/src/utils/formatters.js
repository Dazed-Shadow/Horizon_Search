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

export function deadlineStatus(deadlineStr) {
  if (!deadlineStr) return null;
  const now = new Date();
  const deadline = new Date(deadlineStr);
  const diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { label: "Closed", color: "text-red-600" };
  if (diffDays <= 3) return { label: `${diffDays}d left`, color: "text-red-500 font-semibold" };
  if (diffDays <= 7) return { label: `${diffDays}d left`, color: "text-orange-500 font-semibold" };
  if (diffDays <= 14) return { label: `${diffDays}d left`, color: "text-yellow-600" };
  return { label: `${diffDays}d left`, color: "text-gray-500" };
}

export function buildQueryString(params) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== "" && v !== null && v !== undefined) q.set(k, v);
  });
  return q.toString();
}
