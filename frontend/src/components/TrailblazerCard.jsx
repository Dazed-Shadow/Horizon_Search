import React from "react";

const TAG_COLORS = {
  "Army":          "bg-green-100 text-green-800",
  "Marine Corps":  "bg-red-100 text-red-800",
  "Navy SEALs":    "bg-blue-100 text-blue-800",
  "Special Forces":"bg-amber-100 text-amber-800",
  "Leadership":    "bg-indigo-100 text-indigo-800",
  "Consulting":    "bg-indigo-100 text-indigo-800",
  "Fortune 500":   "bg-purple-100 text-purple-800",
  "Logistics":     "bg-purple-100 text-purple-800",
  "Manufacturing": "bg-gray-100 text-gray-700",
  "Podcast":       "bg-orange-100 text-orange-800",
  "Author":        "bg-teal-100 text-teal-800",
  "Nonprofit":     "bg-green-100 text-green-800",
  "Entertainment": "bg-pink-100 text-pink-800",
  "Film":          "bg-pink-100 text-pink-800",
  "Arts":          "bg-pink-100 text-pink-800",
  "Social Media":  "bg-orange-100 text-orange-800",
  "SDVOSB":        "bg-green-100 text-green-800",
};

export default function TrailblazerCard({ figure, onOpen }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(figure)}
      className="group w-full text-left bg-white rounded-2xl border border-gray-200 shadow-sm
                 hover:shadow-md hover:border-brand-200 transition-all overflow-hidden"
    >
      {/* Color band top */}
      <div className={`${figure.avatarColor} h-2 w-full`} />

      <div className="p-5">
        {/* Avatar + name */}
        <div className="flex items-center gap-4 mb-4">
          <div className={`${figure.avatarColor} shrink-0 w-14 h-14 rounded-xl flex items-center
                           justify-center text-white font-bold text-lg select-none`}>
            {figure.initials}
          </div>
          <div className="min-w-0">
            <p className="font-bold text-gray-900 leading-tight">{figure.name}</p>
            <p className="text-xs text-gray-500 mt-0.5">{figure.branch}</p>
            <p className="text-xs text-gray-400">{figure.yearsServed} · {figure.era}</p>
          </div>
        </div>

        {/* Role */}
        <p className="text-xs font-semibold text-brand-600 mb-2">{figure.role}</p>

        {/* Hook */}
        <p className="text-sm text-gray-600 leading-relaxed line-clamp-3 mb-4">
          {figure.oneLineHook}
        </p>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {figure.tags.slice(0, 3).map(tag => (
            <span key={tag}
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${TAG_COLORS[tag] ?? "bg-gray-100 text-gray-600"}`}>
              {tag}
            </span>
          ))}
        </div>

        {/* CTA */}
        <p className="text-xs font-semibold text-brand-600 group-hover:text-brand-700 group-hover:underline">
          Read full story →
        </p>
      </div>
    </button>
  );
}
