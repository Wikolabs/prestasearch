import type { SearchResult } from "../types";

interface Props {
  result: SearchResult;
}

function scoreInfo(score: number): { label: string; classes: string } {
  if (score >= 0.85) return { label: "Excellent", classes: "bg-emerald-500 text-white" };
  if (score >= 0.7) return { label: "Good match", classes: "bg-amber-500 text-white" };
  if (score >= 0.5) return { label: "Fair match", classes: "bg-orange-400 text-white" };
  return { label: "Low match", classes: "bg-gray-400 text-white" };
}

export default function ProviderCard({ result }: Props) {
  const { prestataire, similarity_score } = result;
  const pct = Math.round(similarity_score * 100);
  const { label, classes } = scoreInfo(similarity_score);

  return (
    <div className="group bg-white rounded-2xl shadow-sm hover:shadow-md border border-gray-100 overflow-hidden flex flex-col transition-all duration-200 hover:-translate-y-0.5">
      <div className="relative overflow-hidden">
        {prestataire.image_base64 ? (
          <img
            src={`data:image/jpeg;base64,${prestataire.image_base64}`}
            alt={prestataire.name}
            className="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-44 bg-gradient-to-br from-amber-50 to-orange-50 flex items-center justify-center">
            <svg className="w-12 h-12 text-amber-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
        )}
        <span className={`absolute top-3 right-3 text-xs font-semibold px-2.5 py-1 rounded-full shadow ${classes}`}>
          {pct}%
        </span>
      </div>
      <div className="p-4 flex flex-col flex-1">
        <div className="mb-2">
          <h3 className="font-semibold text-gray-900 text-sm leading-snug">{prestataire.name}</h3>
          <p className="text-xs font-medium text-amber-600 mt-0.5">{prestataire.specialty}</p>
          {prestataire.city && (
            <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
              <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
              </svg>
              {prestataire.city}{prestataire.country ? `, ${prestataire.country}` : ""}
            </p>
          )}
        </div>
        <p className="text-gray-500 text-xs mb-3 line-clamp-2 flex-1 leading-relaxed">
          {prestataire.description}
        </p>
        {prestataire.services.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {prestataire.services.slice(0, 3).map((s) => (
              <span key={s} className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded-lg font-medium">
                {s}
              </span>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-50">
          {prestataire.hourly_rate > 0 ? (
            <p className="text-amber-600 font-bold text-lg">
              {prestataire.hourly_rate.toFixed(0)}<span className="text-xs font-normal text-gray-400 ml-1">$/h</span>
            </p>
          ) : (
            <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-md">{label}</span>
          )}
          {prestataire.rating > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-amber-400 text-sm leading-none">{"★".repeat(Math.round(prestataire.rating))}</span>
              <span className="text-xs text-gray-500 font-medium">{prestataire.rating.toFixed(1)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
