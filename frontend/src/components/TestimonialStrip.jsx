import { useState, useEffect, useCallback } from "react";
import { testimonials, founderNote } from "../data/testimonials";

const CERT_COLORS = {
  SDVOSB: "bg-green-100 text-green-800",
  VOSB:   "bg-green-100 text-green-800",
  "8AN":  "bg-blue-100 text-blue-800",
  HZC:    "bg-blue-100 text-blue-800",
  WOSB:   "bg-purple-100 text-purple-800",
  SBA:    "bg-gray-100 text-gray-700",
};

export default function TestimonialStrip() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);

  const advance = useCallback(() => {
    setActive(i => (i + 1) % testimonials.length);
  }, []);

  // Auto-rotate every 6 seconds; pause on hover so users can read
  useEffect(() => {
    if (paused || testimonials.length <= 1) return;
    const id = setInterval(advance, 6000);
    return () => clearInterval(id);
  }, [paused, advance]);

  const t = testimonials[active];

  return (
    <div className="bg-brand-900/60 border-t border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <div className="flex flex-col sm:flex-row gap-6 items-start">

          {/* Rotating veteran quote */}
          <div
            className="flex-1 min-w-0"
            onMouseEnter={() => setPaused(true)}
            onMouseLeave={() => setPaused(false)}
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-300 mb-2">
              From the veteran business community
            </p>
            <blockquote className="text-white/90 text-sm leading-relaxed italic mb-3">
              "{t.quote}"
            </blockquote>
            <div className="flex items-center gap-3 flex-wrap">
              <div>
                <p className="text-white font-semibold text-sm">{t.name}</p>
                <p className="text-brand-300 text-xs">{t.company} · {t.state}</p>
              </div>
              {t.certification && (
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${CERT_COLORS[t.certification] ?? "bg-gray-100 text-gray-700"}`}>
                  {t.certification}
                </span>
              )}
              {t.sourceUrl && (
                <a href={t.sourceUrl} target="_blank" rel="noopener noreferrer"
                  className="text-xs text-brand-300 hover:text-white hover:underline">
                  Read their story ↗
                </a>
              )}
            </div>

            {/* Dot navigation */}
            {testimonials.length > 1 && (
              <div className="flex gap-1.5 mt-3">
                {testimonials.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActive(i)}
                    aria-label={`Testimonial ${i + 1}`}
                    className={`w-1.5 h-1.5 rounded-full transition-all ${
                      i === active ? "bg-white w-4" : "bg-white/30 hover:bg-white/60"
                    }`}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="hidden sm:block w-px bg-white/10 self-stretch" />

          {/* Founder note — always visible */}
          <div className="sm:w-72 shrink-0">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-300 mb-2">
              Why we built this
            </p>
            <p className="text-white/80 text-sm leading-relaxed italic mb-2">
              "{founderNote.message}"
            </p>
            <p className="text-white font-semibold text-xs">{founderNote.name}</p>
            <p className="text-brand-300 text-xs">{founderNote.role}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
