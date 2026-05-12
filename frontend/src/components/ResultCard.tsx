import type { CalculResult } from "../types";

interface ResultCardProps {
  result: CalculResult;
  recapChassis: string;
  recapLargeur: number;
  recapHauteur: number;
  recapCouleur: string;
  recapCouleurHex: string;
}

// Gauge bar: 0-5 W/(m²·K) for Uw, 0-1 for Sw/Tlw
function GaugeBar({ value, max, low }: { value: number; max: number; low?: boolean }) {
  const pct = Math.min(100, (value / max) * 100);
  const color = low
    ? pct < 33 ? "#22c55e" : pct < 66 ? "#f59e0b" : "#ef4444"
    : pct > 66 ? "#22c55e" : pct > 33 ? "#f59e0b" : "#ef4444";
  return (
    <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
      <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

function MetricCard({
  code, label, value, unit, description, max, low, highlight,
}: {
  code: string;
  label: string;
  value: number | null | undefined;
  unit: string;
  description: string;
  max: number;
  low?: boolean;
  highlight?: boolean;
}) {
  const displayed = value !== null && value !== undefined
    ? value.toFixed(value >= 10 ? 1 : 2)
    : "—";

  return (
    <div className={`rounded-2xl p-5 flex flex-col gap-1 ${highlight ? "bg-janneau-teal text-white" : "bg-white border border-gray-200"}`}>
      <div className={`text-3xl font-bold tracking-tight ${highlight ? "text-white" : "text-janneau-dark"}`}>
        {displayed}
      </div>
      <div className={`text-xs font-medium ${highlight ? "text-white/70" : "text-gray-400"}`}>{unit}</div>
      <div className={`text-sm font-semibold mt-1 ${highlight ? "text-white" : "text-gray-700"}`}>
        <span className="font-bold">{code}</span> — {label}
      </div>
      <div className={`text-xs leading-snug ${highlight ? "text-white/60" : "text-gray-400"}`}>{description}</div>
      {value !== null && value !== undefined && (
        <GaugeBar value={value} max={max} low={low} />
      )}
    </div>
  );
}

export function ResultCard({
  result, recapChassis, recapLargeur, recapHauteur, recapCouleur, recapCouleurHex,
}: ResultCardProps) {
  const { menuiserie_seule: m, avec_volet: v, details: d } = result;

  return (
    <div className="space-y-5">

      {/* Récapitulatif paramètres */}
      <div className="bg-janneau-dark text-white rounded-2xl px-6 py-4 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-0">
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Menuiserie calculée</div>
          <div className="font-semibold text-sm truncate">{recapChassis}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">Largeur</div>
          <div className="font-semibold text-sm">{recapLargeur} mm</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">Hauteur</div>
          <div className="font-semibold text-sm">{recapHauteur} mm</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">Surface</div>
          <div className="font-semibold text-sm">{d.surface_totale?.toFixed(2)} m²</div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="w-6 h-6 rounded border border-white/20 flex-shrink-0"
            style={{ backgroundColor: recapCouleurHex }}
          />
          <div>
            <div className="text-xs text-gray-400 mb-0.5">Couleur</div>
            <div className="text-xs font-medium max-w-[100px] truncate">{recapCouleur}</div>
          </div>
        </div>
      </div>

      {/* 3 métriques principales */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
          Menuiserie seule
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <MetricCard
            code={m.label_uw}
            label="Transmission thermique"
            value={m.Uw}
            unit="W/(m²·K)"
            description="Plus la valeur est basse, meilleure est l'isolation thermique"
            max={3.5}
            low
            highlight
          />
          <MetricCard
            code="Sw"
            label="Facteur solaire"
            value={m.Sw}
            unit="sans unité (0 à 1)"
            description="Part du rayonnement solaire total transmis à travers la menuiserie"
            max={1}
          />
          <MetricCard
            code="TLw"
            label="Transmission lumineuse"
            value={m.Tlw}
            unit="%"
            description="Part de lumière naturelle transmise — plus c'est élevé, plus c'est lumineux"
            max={100}
          />
        </div>
      </div>

      {/* Volet roulant */}
      {v && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
            Avec volet roulant
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { code: "rR", label: "Résistance volet", value: v.rR, unit: "m²·K/W" },
              { code: "Ujn", label: "Uw + volet (nuit)", value: v.Ujn, unit: "W/(m²·K)" },
              ...(v.Uc !== null ? [{ code: "Uc", label: "Transmittance coffre", value: v.Uc, unit: "W/(m²·K)" }] : []),
              ...(v.Ubb_jn !== null ? [{ code: "Ubb.jn", label: "Ubb nuit (ensemble)", value: v.Ubb_jn, unit: "W/(m²·K)" }] : []),
            ].map((item) => (
              <div key={item.code} className="bg-white border border-gray-200 rounded-2xl p-4 text-center">
                <div className="text-2xl font-bold text-janneau-dark">
                  {item.value !== null && item.value !== undefined ? item.value.toFixed(4) : "—"}
                </div>
                <div className="text-xs text-gray-400 mt-0.5">{item.unit}</div>
                <div className="text-xs font-semibold text-gray-600 mt-1">
                  <span className="font-bold">{item.code}</span> — {item.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Détails techniques */}
      <details className="bg-gray-50 border border-gray-200 rounded-2xl overflow-hidden">
        <summary className="px-5 py-3 cursor-pointer text-sm font-medium text-gray-600 hover:text-janneau-teal flex items-center gap-2">
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
          </svg>
          Détails du calcul
        </summary>
        <div className="px-5 pb-4 pt-2 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-gray-500">
          <div><span className="font-semibold text-gray-700">Type géo.</span><br /><code className="font-mono text-[10px]">{d.geo_type}</code></div>
          <div><span className="font-semibold text-gray-700">Uf moyen</span><br />{d.Uf_moyen?.toFixed(4)} W/(m²·K)</div>
          <div><span className="font-semibold text-gray-700">Af total</span><br />{d.Af_total?.toFixed(4)} m²</div>
          <div><span className="font-semibold text-gray-700">Ag total</span><br />{d.Ag_total?.toFixed(4)} m²</div>
          <div className="col-span-2 sm:col-span-4 border-t border-gray-200 pt-2 text-gray-400">
            {d.normes.join(" · ")}
          </div>
        </div>
      </details>
    </div>
  );
}
