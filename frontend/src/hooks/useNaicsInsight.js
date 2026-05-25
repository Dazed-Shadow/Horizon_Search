import { useState, useCallback } from "react";

export function useNaicsInsight() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeKey, setActiveKey] = useState(null);

  const fetchInsight = useCallback(async (naicsCode, setAside = null) => {
    const key = `${naicsCode}:${setAside || ""}`;
    if (key === activeKey && data) return; // already loaded for this combo

    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ naics_code: naicsCode });
    if (setAside) params.set("set_aside", setAside);
    try {
      const res = await fetch(`/api/insights/naics-activity?${params}`);
      const text = await res.text();
      let body;
      try {
        body = JSON.parse(text);
      } catch {
        throw new Error("Backend server is not responding — make sure it is running on port 8000.");
      }
      if (!res.ok) {
        throw new Error(body.detail || `Error ${res.status}`);
      }
      setData(body);
      setActiveKey(key);
    } catch (err) {
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [activeKey, data]);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
    setActiveKey(null);
  }, []);

  return { data, loading, error, fetchInsight, clear };
}
