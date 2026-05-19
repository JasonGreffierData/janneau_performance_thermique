import type { CalculResult } from "../types";

interface ResultCardProps {
  result: CalculResult;
  recapFamille: string;
  recapChassis: string;
  recapLargeur: number;
  recapHauteur: number;
  recapCouleur: string;
  recapCouleurHex: string;
}

type GaugeConfig = {
  max: number;
  thresholds: [number, number];   // [seuil_bon, seuil_passable]
  low: boolean;                   // true = valeur basse = meilleure
  labels: [string, string, string]; // [bon, passable, mauvais]
  reference?: string;             // ex: "RE2020 : ≤ 1.3"
};

function GaugeBar({ value, cfg, highlight }: { value: number; cfg: GaugeConfig; highlight?: boolean }) {
  const pct = Math.min(100, (value / cfg.max) * 100);
  const [t1, t2] = cfg.thresholds;

  let color: string;
  let perfLabel: string;
  if (cfg.low) {
    if (value <= t1)      { color = "#22c55e"; perfLabel = cfg.labels[0]; }
    else if (value <= t2) { color = "#f59e0b"; perfLabel = cfg.labels[1]; }
    else                  { color = "#ef4444"; perfLabel = cfg.labels[2]; }
  } else {
    if (value >= t1)      { color = "#22c55e"; perfLabel = cfg.labels[0]; }
    else if (value >= t2) { color = "#f59e0b"; perfLabel = cfg.labels[1]; }
    else                  { color = "#ef4444"; perfLabel = cfg.labels[2]; }
  }

  return (
    <div className="mt-2 space-y-1">
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 bg-black/10 rounded-full h-1.5">
          <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
        </div>
        <span className={`text-[10px] font-semibold whitespace-nowrap ${highlight ? "text-white/80" : "text-gray-500"}`}
          style={{ color: highlight ? undefined : color }}>
          {perfLabel}
        </span>
      </div>
      {cfg.reference && (
        <p className={`text-[10px] ${highlight ? "text-white/50" : "text-gray-400"}`}>{cfg.reference}</p>
      )}
    </div>
  );
}

function MetricCard({
  code, label, value, unit, description, cfg, highlight,
}: {
  code: string;
  label: string;
  value: number | null | undefined;
  unit: string;
  description: string;
  cfg: GaugeConfig;
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
        <GaugeBar value={value} cfg={cfg} highlight={highlight} />
      )}
    </div>
  );
}

export function ResultCard({
  result, recapFamille, recapChassis, recapLargeur, recapHauteur, recapCouleur, recapCouleurHex,
}: ResultCardProps) {
  const { menuiserie_seule: m, avec_volet: v, details: d } = result;

  return (
    <div className="space-y-5">

      {/* Récapitulatif paramètres */}
      <div className="bg-janneau-dark text-white rounded-2xl px-6 py-4 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-0">
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Menuiserie calculée</div>
          <div className="text-xs text-janneau-teal font-medium mb-0.5">{recapFamille}</div>
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
            cfg={{
              max: 3.5,
              thresholds: [1.3, 2.0],
              low: true,
              labels: ["Très performant", "Réglementaire", "Insuffisant"],
              reference: "Réf. RE2020 : ≤ 1,3 W/(m²·K)",
            }}
            highlight
          />
          <MetricCard
            code="Sw"
            label="Facteur solaire"
            value={m.Sw}
            unit="sans unité (0 à 1)"
            description="Part du rayonnement solaire transmis — dépend de l'orientation et du climat"
            cfg={{
              max: 1,
              thresholds: [0.6, 0.3],
              low: false,
              labels: ["Élevé", "Moyen", "Faible"],
            }}
          />
          <MetricCard
            code="TLw"
            label="Transmission lumineuse"
            value={m.Tlw}
            unit="%"
            description="Part de lumière naturelle transmise — plus c'est élevé, plus c'est lumineux"
            cfg={{
              max: 100,
              thresholds: [65, 45],
              low: false,
              labels: ["Très lumineux", "Lumineux", "Peu lumineux"],
            }}
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
        <div className="px-5 pb-4 pt-2 space-y-3 text-xs text-gray-500">

          {/* Géométrie */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div><span className="font-semibold text-gray-700">Type géo.</span><br /><code className="font-mono text-[10px]">{d.geo_type}</code></div>
            <div><span className="font-semibold text-gray-700">Uf moyen</span><br />{d.Uf_moyen?.toFixed(4)} W/(m²·K)</div>
            <div><span className="font-semibold text-gray-700">Af total</span><br />{d.Af_total?.toFixed(4)} m²</div>
            <div><span className="font-semibold text-gray-700">Ag total</span><br />{d.Ag_total?.toFixed(4)} m²</div>
          </div>

          {/* Vitrages par zone */}
          {d.zones_vitrage.length > 0 && (
            <div className="border-t border-gray-200 pt-2">
              <p className="font-semibold text-gray-700 mb-1.5">Remplissages</p>
              <div className="overflow-x-auto">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="text-gray-400 border-b border-gray-100">
                      <th className="text-left font-medium pb-1 pr-3">Zone</th>
                      <th className="text-right font-medium pb-1 pr-3">Ug <span className="font-normal">(W/m²·K)</span></th>
                      <th className="text-right font-medium pb-1 pr-3">Ψg <span className="font-normal">(W/m·K)</span></th>
                      <th className="text-right font-medium pb-1">Sg</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.zones_vitrage.map((z) => (
                      <tr key={z.zone} className="border-b border-gray-50">
                        <td className="py-1 pr-3 font-semibold text-gray-600">{z.zone}</td>
                        <td className="py-1 pr-3 text-right">{z.Ug.toFixed(3)}</td>
                        <td className="py-1 pr-3 text-right">{z.Psi_g.toFixed(4)}</td>
                        <td className="py-1 text-right">{z.Sg != null ? z.Sg.toFixed(3) : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Constantes utilisées */}
          <div className="border-t border-gray-200 pt-2">
            <p className="font-semibold text-gray-700 mb-1.5">Constantes de calcul</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <div><span className="font-medium text-gray-600">α couleur</span><br />{d.alpha?.toFixed(2)} <span className="text-gray-400">(XP P50-777)</span></div>
              <div><span className="font-medium text-gray-600">he</span><br />{d.HE} W/(m²·K) <span className="text-gray-400">(EN ISO 6946)</span></div>
              <div><span className="font-medium text-gray-600">Ψg défaut</span><br />{d.Psi_g_defaut} W/(m·K) <span className="text-gray-400">(intercalaire alu)</span></div>
            </div>
          </div>

          {/* Normes */}
          <div className="border-t border-gray-200 pt-2 text-gray-400">
            {d.normes.join(" · ")}
          </div>
        </div>
      </details>
    </div>
  );
}
