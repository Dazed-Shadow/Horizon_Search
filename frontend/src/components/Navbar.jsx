import React, { useState } from "react";
import { NavLink } from "react-router-dom";

const NAV_LINKS = [
  { to: "/",              label: "Search Contracts" },
  { to: "/insights",      label: "Market Intel" },
  { to: "/mission",       label: "Mission" },
  { to: "/trailblazers",  label: "Trailblazers" },
  { to: "/licensing",     label: "Licensing & Certs" },
  { to: "/primer",        label: "How to Win" },
];

// "Start Here" is visually separate — a green CTA pill for newcomers who don't know where to begin.
const START_LINK = { to: "/start", label: "Start Here" };

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="bg-brand-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-3 shrink-0">
            <div className="bg-white/10 rounded-lg p-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
              </svg>
            </div>
            <div className="leading-tight">
              <p className="font-bold text-base tracking-tight">Horizon Search</p>
              <p className="text-[10px] text-brand-200">Matching services to those who serve</p>
            </div>
          </NavLink>

          {/* Desktop nav */}
          <nav className="hidden sm:flex items-center gap-1">
            {NAV_LINKS.map(link => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `px-4 py-2 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "text-brand-100 hover:bg-white/10 hover:text-white"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
            <NavLink
              to={START_LINK.to}
              className={({ isActive }) =>
                `ml-2 px-4 py-2 rounded-lg text-sm font-bold transition border ${
                  isActive
                    ? "bg-green-500 text-white border-green-400"
                    : "bg-green-600/30 text-green-200 border-green-500/40 hover:bg-green-600/50 hover:text-white"
                }`
              }
            >
              {START_LINK.label}
            </NavLink>
          </nav>

          {/* Mobile hamburger */}
          <button
            className="sm:hidden p-2 rounded-lg hover:bg-white/10 transition"
            onClick={() => setMobileOpen(o => !o)}
            aria-label="Toggle menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              }
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <nav className="sm:hidden pb-3 space-y-1">
            {NAV_LINKS.map(link => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `block px-4 py-2 rounded-lg text-sm font-medium transition ${
                    isActive ? "bg-white/20 text-white" : "text-brand-100 hover:bg-white/10"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
            <NavLink
              to={START_LINK.to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `block px-4 py-2 rounded-lg text-sm font-bold transition ${
                  isActive ? "bg-green-500 text-white" : "text-green-300 hover:bg-green-600/30"
                }`
              }
            >
              {START_LINK.label}
            </NavLink>
          </nav>
        )}
      </div>
    </header>
  );
}
