import { useState, useEffect } from "react";

function compute(deadlineStr) {
  if (!deadlineStr) return null;
  const diff = new Date(deadlineStr).getTime() - Date.now();
  if (diff < 0) return { text: "Closed", color: "text-red-600 font-semibold" };
  const days = Math.floor(diff / 86_400_000);
  const hours = Math.floor((diff % 86_400_000) / 3_600_000);
  if (days === 0 && hours === 0) return { text: "< 1 hour left", color: "text-red-500 font-bold" };
  if (days === 0)  return { text: `${hours}h left`,        color: "text-red-500 font-bold" };
  if (days <= 3)   return { text: `${days}d ${hours}h left`, color: "text-red-500 font-semibold" };
  if (days <= 7)   return { text: `${days}d ${hours}h left`, color: "text-orange-500 font-semibold" };
  if (days <= 14)  return { text: `${days}d left`,          color: "text-yellow-600 font-medium" };
  return { text: `${days}d left`, color: "text-gray-600" };
}

export default function LiveCountdown({ deadline }) {
  const [status, setStatus] = useState(() => compute(deadline));

  useEffect(() => {
    setStatus(compute(deadline));
    if (!deadline) return;
    const id = setInterval(() => setStatus(compute(deadline)), 60_000);
    return () => clearInterval(id);
  }, [deadline]);

  if (!deadline || !status) {
    return <span className="text-gray-400">Not specified</span>;
  }
  return <span className={status.color}>{status.text}</span>;
}
