import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Link } from "react-router-dom";
import { trailblazers } from "../data/trailblazers";
import TrailblazerCard from "../components/TrailblazerCard";
import TrailblazerDrawer from "../components/TrailblazerDrawer";
import ArticleList from "../components/ArticleList";

export default function TrailblazersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeFigure, setActiveFigure] = useState(null);

  // Deep-link: ?figure=jocko-willink opens that drawer on load + share
  useEffect(() => {
    const slug = searchParams.get("figure");
    if (slug) {
      const found = trailblazers.find(f => f.slug === slug);
      if (found) setActiveFigure(found);
    }
  }, []);

  // Update document title + URL when drawer opens/closes
  function openFigure(figure) {
    setActiveFigure(figure);
    setSearchParams({ figure: figure.slug });
    document.title = `${figure.name} — Horizon Search Trailblazers`;
  }

  function closeFigure() {
    setActiveFigure(null);
    setSearchParams({});
    document.title = "Trailblazers — Horizon Search";
  }

  useEffect(() => {
    document.title = "Trailblazers — Horizon Search";
    return () => { document.title = "Horizon Search"; };
  }, []);

  return (
    <div className="flex flex-col">

      <TrailblazerDrawer figure={activeFigure} onClose={closeFigure} />

      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <div className="relative bg-gradient-to-br from-gray-900 via-brand-900 to-gray-900 overflow-hidden">
        {/* Decorative rings */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 right-0 w-72 h-72 bg-brand-600/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
          <div className="absolute bottom-0 left-0 w-72 h-72 bg-green-900/30 rounded-full blur-3xl translate-y-1/2 -translate-x-1/4" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 text-white/80 border border-white/20
                          rounded-full px-4 py-1.5 text-sm font-semibold mb-5">
            <svg className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Veteran Trailblazers
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight mb-5">
            Builders. Operators. Storytellers.
          </h1>

          <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto mb-3">
            Veterans have been building America's most important companies, nonprofits,
            and cultural institutions for generations.
          </p>
          <p className="text-gray-400 text-base leading-relaxed max-w-xl mx-auto mb-8">
            These are their stories — and the books, articles, and resources that carry
            their lessons forward for the next generation of veteran entrepreneurs.
          </p>

          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/"
              className="bg-white text-brand-700 font-bold px-6 py-3 rounded-xl hover:bg-brand-50 transition text-sm">
              Search active contracts →
            </Link>
            <Link to="/start"
              className="bg-white/10 text-white border border-white/20 font-bold px-6 py-3 rounded-xl
                         hover:bg-white/20 transition text-sm">
              Start Here guide →
            </Link>
          </div>
        </div>
      </div>

      {/* ── Trailblazer grid ──────────────────────────────────────────── */}
      <div className="bg-gray-50 py-14">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Great Figures</h2>
            <p className="text-gray-500 text-sm max-w-xl mx-auto">
              Click any card to read the full bio, books, and related articles.
              Each profile links to a shareable URL — pass it on.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {trailblazers.map(figure => (
              <TrailblazerCard key={figure.slug} figure={figure} onOpen={openFigure} />
            ))}
          </div>

          <div className="mt-10 bg-white rounded-2xl border border-gray-200 px-6 py-5 flex flex-col
                          sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="font-semibold text-gray-800 text-sm">Know a veteran who belongs here?</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Suggest a figure — entrepreneur, creator, public servant, athlete. Any branch, any era.
              </p>
            </div>
            <a href="mailto:the.riveraj@gmail.com?subject=Trailblazer suggestion"
              className="shrink-0 bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm
                         px-5 py-2.5 rounded-xl transition">
              Suggest a Trailblazer →
            </a>
          </div>
        </div>
      </div>

      {/* ── Articles & Resources ─────────────────────────────────────── */}
      <div className="bg-white py-14 border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <ArticleList />
        </div>
      </div>

      {/* ── Bottom CTA ───────────────────────────────────────────────── */}
      <div className="bg-brand-900 py-12">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <h2 className="text-xl font-bold text-white mb-3">
            Their path is your path.
          </h2>
          <p className="text-brand-200 text-sm mb-6 leading-relaxed">
            Every figure on this page built something post-service.
            Federal contracting is one of the most direct paths to doing the same.
          </p>
          <Link to="/start"
            className="inline-block bg-white text-brand-700 font-bold px-6 py-3 rounded-xl
                       hover:bg-brand-50 transition text-sm">
            Start your road map →
          </Link>
        </div>
      </div>

    </div>
  );
}
