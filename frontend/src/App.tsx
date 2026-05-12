import { useRef, useState } from "react";
import { api } from "./api/client";
import { NumberInput } from "./components/NumberInput";
import { ResultCard } from "./components/ResultCard";
import { VitrageRow } from "./components/VitrageRow";
import { Select } from "./components/Select";
import {
  useChassis,
  useCouleurs,
  useFamilles,
  useIntercalaires,
  useVitrages,
  useVolets,
} from "./hooks/useReferentiels";
import type { CalculResult, VitragInput, VoletInput } from "./types";
import { colorHex, isLight } from "./utils/ralColors";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ISOLATION_OPTIONS = [
  { value: "T", label: "T — Non isolé" },
  { value: "P0", label: "P0" },
  { value: "P1", label: "P1" },
  { value: "P2", label: "P2" },
  { value: "P3", label: "P3" },
  { value: "P4", label: "P4 — Très isolé" },
];

const DEFAULT_INTERCALAIRE = "Warm-Edge";

const FAMILLE_ICONS: Record<string, JSX.Element> = {
  "FENETRES A FRAPPE": (
    <svg viewBox="0 0 80 80" className="w-16 h-16" fill="none" stroke="currentColor" strokeWidth="2.5">
      <rect x="8" y="8" width="64" height="64" rx="2" />
      <line x1="40" y1="8" x2="40" y2="72" />
      <line x1="8" y1="40" x2="72" y2="40" />
      <circle cx="38" cy="40" r="2.5" fill="currentColor" stroke="none" />
    </svg>
  ),
  "FENETRES COULISSANTES": (
    <svg viewBox="0 0 80 80" className="w-16 h-16" fill="none" stroke="currentColor" strokeWidth="2.5">
      <rect x="8" y="8" width="64" height="64" rx="2" />
      <line x1="40" y1="8" x2="40" y2="72" />
      <polyline points="28,36 20,40 28,44" />
      <polyline points="52,36 60,40 52,44" />
    </svg>
  ),
  "PORTES": (
    <svg viewBox="0 0 80 80" className="w-16 h-16" fill="none" stroke="currentColor" strokeWidth="2.5">
      <rect x="18" y="8" width="44" height="64" rx="2" />
      <rect x="24" y="16" width="32" height="20" rx="1" />
      <circle cx="55" cy="42" r="2.5" fill="currentColor" stroke="none" />
    </svg>
  ),
  "BAIES COULISSANTES": (
    <svg viewBox="0 0 80 80" className="w-16 h-16" fill="none" stroke="currentColor" strokeWidth="2.5">
      <rect x="4" y="12" width="72" height="56" rx="2" />
      <line x1="40" y1="12" x2="40" y2="68" />
      <polyline points="28,36 18,40 28,44" />
      <polyline points="52,36 62,40 52,44" />
    </svg>
  ),
};

function getFamilleIcon(famille: string): JSX.Element {
  for (const key of Object.keys(FAMILLE_ICONS)) {
    if (famille.toUpperCase().includes(key.split(" ")[0])) return FAMILLE_ICONS[key];
  }
  return FAMILLE_ICONS["FENETRES A FRAPPE"];
}

// Simple window diagram based on geo_type
function WindowDiagram({ geoType }: { geoType?: string }) {
  const gt = geoType ?? "";
  const panels =
    gt.includes("4_vantaux") ? 4
    : gt.includes("3_vantaux") ? 3
    : gt.includes("2_vantaux_2_fixes") ? 4
    : gt.includes("2_vantaux_1_fixe") ? 3
    : gt.includes("2_vantaux") ? 2
    : gt.includes("imposte") ? 2
    : 1;
  const hasImposte = gt.includes("imposte");

  return (
    <svg viewBox="0 0 60 60" className="w-14 h-14" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="4" y={hasImposte ? 18 : 4} width="52" height={hasImposte ? 38 : 52} rx="1.5" />
      {hasImposte && <rect x="4" y="4" width="52" height="16" rx="1.5" />}
      {panels > 1 && Array.from({ length: panels - 1 }).map((_, i) => (
        <line
          key={i}
          x1={4 + ((i + 1) * 52) / panels}
          y1={hasImposte ? 18 : 4}
          x2={4 + ((i + 1) * 52) / panels}
          y2={hasImposte ? 56 : 56}
        />
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeVitrag(zone: string): VitragInput {
  return { zone, composition: "", intercalaire: DEFAULT_INTERCALAIRE };
}

function nbZonesFromGeoType(geoType: string): { vitrages: number; panneaux: number } {
  if (geoType.startsWith("porte_soubassement")) return { vitrages: 1, panneaux: 1 };
  if (geoType === "1_vantail" || geoType === "1_vantail_traverse_intermediaire") return { vitrages: 1, panneaux: 0 };
  if (geoType === "1_vantail_imposte") return { vitrages: 2, panneaux: 0 };
  if (geoType === "2_vantaux") return { vitrages: 2, panneaux: 0 };
  if (geoType === "3_vantaux") return { vitrages: 3, panneaux: 0 };
  if (geoType === "4_vantaux") return { vitrages: 4, panneaux: 0 };
  if (geoType === "2_vantaux_1_fixe_lateral") return { vitrages: 3, panneaux: 0 };
  if (geoType === "2_vantaux_2_fixes_lateraux") return { vitrages: 4, panneaux: 0 };
  return { vitrages: 1, panneaux: 0 };
}

// ---------------------------------------------------------------------------
// Step section wrapper
// ---------------------------------------------------------------------------

function StepSection({
  number, title, active, children,
}: {
  number: number;
  title: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
        active
          ? "border-janneau-teal shadow-md"
          : "border-gray-200 opacity-50 pointer-events-none"
      }`}
    >
      <div className={`flex items-center gap-3 px-6 py-4 ${active ? "bg-janneau-teal-light" : "bg-gray-50"}`}>
        <span
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
            active ? "bg-janneau-teal text-white" : "bg-gray-300 text-gray-500"
          }`}
        >
          {number}
        </span>
        <h2 className={`font-semibold text-base uppercase tracking-wide ${active ? "text-janneau-teal-dark" : "text-gray-400"}`}>
          {title}
        </h2>
      </div>
      {active && <div className="p-6">{children}</div>}
    </section>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  const familles = useFamilles();
  const [famille, setFamille] = useState("");
  const chassisList = useChassis(famille || null);

  const [chassisNom, setChassisNom] = useState("");
  const selectedChassis = chassisList.find((c) => c.nom === chassisNom) ?? null;

  const vitrages = useVitrages();
  const intercalaires = useIntercalaires();
  const couleurs = useCouleurs();
  const volets = useVolets(selectedChassis?.gamme_code);

  const [couleur, setCouleur] = useState("");
  const [hauteur, setHauteur] = useState<number | "">("");
  const [largeur, setLargeur] = useState<number | "">("");

  const [vitragInputs, setVitragInputs] = useState<VitragInput[]>([]);
  const [panneauInputs, setPanneauInputs] = useState<VitragInput[]>([]);

  const [voletInput, setVoletInput] = useState<VoletInput>({
    actif: false,
    type: null,
    isolation_acoustique: "T",
  });

  const [result, setResult] = useState<CalculResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const resultRef = useRef<HTMLDivElement>(null);

  function handleChassisChange(nom: string) {
    setChassisNom(nom);
    setResult(null);
    const ch = chassisList.find((c) => c.nom === nom);
    if (!ch) { setVitragInputs([]); setPanneauInputs([]); return; }
    setVitragInputs([makeVitrag("G1")]);
    setPanneauInputs([]);
  }

  function syncZones(res: CalculResult) {
    const geoType = res.details.geo_type;
    const { vitrages: nbV, panneaux: nbP } = nbZonesFromGeoType(geoType);
    setVitragInputs((prev) =>
      Array.from({ length: nbV }, (_, i) => ({ ...(prev[i] ?? makeVitrag(`G${i + 1}`)), zone: `G${i + 1}` }))
    );
    setPanneauInputs((prev) =>
      Array.from({ length: nbP }, (_, i) => ({ ...(prev[i] ?? makeVitrag(`P${i + 1}`)), zone: `P${i + 1}` }))
    );
  }

  async function handleCalculer(e: React.FormEvent) {
    e.preventDefault();
    if (!famille || !chassisNom || !couleur || !hauteur || !largeur) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.calculer({
        famille,
        chassis: chassisNom,
        couleur,
        hauteur_mm: hauteur as number,
        largeur_mm: largeur as number,
        volet: {
          actif: voletInput.actif,
          type: voletInput.actif ? voletInput.type : null,
          isolation_acoustique: voletInput.isolation_acoustique,
        },
        vitrages: vitragInputs.filter((v) => v.composition),
        panneaux: panneauInputs.filter((v) => v.composition),
      });
      setResult(res);
      syncZones(res);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  const selectedVolet = volets.find((v) => v.designation === voletInput.type);
  const isPorte = famille.startsWith("PORTES");

  const canSubmit =
    !!famille &&
    !!chassisNom &&
    selectedChassis?.supporte !== false &&
    !!couleur &&
    !!hauteur &&
    !!largeur;

  const selectedCouleurHex = couleur ? colorHex(couleur) : null;

  // Active step logic
  const step2Active = !!famille;
  const step3Active = step2Active && !!chassisNom;
  const step4Active = step3Active;
  const step5Active = step3Active;
  const step6Active = step3Active;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {/* ── HEADER ─────────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <img src="/logo-janneau.png" alt="Janneau" className="h-10 w-auto" />
          <div className="hidden sm:flex items-center gap-2 text-xs text-gray-400 uppercase tracking-widest">
            <span className="w-2 h-2 rounded-full bg-janneau-teal inline-block" />
            Outil Pro — Calcul thermique
          </div>
        </div>
      </header>

      {/* ── HERO ───────────────────────────────────────────────────────────── */}
      <div className="bg-janneau-dark text-white py-10 px-6">
        <div className="max-w-6xl mx-auto">
          <p className="text-janneau-teal text-xs uppercase tracking-widest font-semibold mb-2">
            Outil réservé aux professionnels
          </p>
          <h1 className="text-2xl sm:text-3xl font-bold leading-snug mb-3">
            Calculateur de performances thermiques
            <br />
            <span className="text-janneau-teal">Thermo-luminosité<sup className="text-sm">®</sup></span>
          </h1>
          <p className="text-gray-300 max-w-2xl text-sm leading-relaxed">
            Calculez instantanément les coefficients <strong className="text-white">Uw</strong> (transmission thermique),{" "}
            <strong className="text-white">Sw</strong> (facteur solaire) et{" "}
            <strong className="text-white">TLw</strong> (transmission lumineuse) de vos menuiseries JANNEAU,
            selon les normes <span className="text-gray-400">EN ISO 10077-1</span> et{" "}
            <span className="text-gray-400">XP P50-777</span>.
          </p>

          {/* 3 indicateurs pedagogy */}
          <div className="grid grid-cols-3 gap-4 mt-6 max-w-xl">
            {[
              { code: "Uw", label: "Transmission thermique", desc: "Plus la valeur est basse, meilleure est l'isolation" },
              { code: "Sw", label: "Facteur solaire", desc: "Part du rayonnement solaire transmis" },
              { code: "TLw", label: "Transmission lumineuse", desc: "Part de lumière naturelle transmise" },
            ].map((m) => (
              <div key={m.code} className="bg-white/10 rounded-xl px-4 py-3 text-center backdrop-blur-sm">
                <div className="text-janneau-teal font-bold text-xl">{m.code}</div>
                <div className="text-white font-semibold text-xs mt-1">{m.label}</div>
                <div className="text-gray-400 text-xs mt-1 hidden sm:block">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── FORM + RESULTS ─────────────────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-5">
        <form onSubmit={handleCalculer} className="space-y-5">

          {/* ── STEP 1 — Famille de produit ─────────────────────────────── */}
          <StepSection number={1} title="Famille de produit" active>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {familles.map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => { setFamille(f); setChassisNom(""); setResult(null); }}
                  className={`rounded-xl border-2 p-4 flex flex-col items-center gap-2 text-center transition-all hover:shadow-md ${
                    famille === f
                      ? "border-janneau-teal bg-janneau-teal-light text-janneau-teal-dark"
                      : "border-gray-200 bg-white text-gray-600 hover:border-janneau-teal/40"
                  }`}
                >
                  <span className={famille === f ? "text-janneau-teal" : "text-gray-400"}>
                    {getFamilleIcon(f)}
                  </span>
                  <span className="text-xs font-semibold leading-tight">{f}</span>
                  {famille === f && (
                    <span className="text-[10px] bg-janneau-teal text-white rounded-full px-2 py-0.5">
                      Sélectionné
                    </span>
                  )}
                </button>
              ))}
            </div>
          </StepSection>

          {/* ── STEP 2 — Type de châssis ─────────────────────────────────── */}
          <StepSection number={2} title="Type de châssis" active={step2Active}>
            {chassisList.length === 0 ? (
              <p className="text-sm text-gray-400 italic">Chargement…</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {chassisList.map((c) => (
                  <button
                    key={c.nom}
                    type="button"
                    disabled={!c.supporte}
                    onClick={() => handleChassisChange(c.nom)}
                    className={`rounded-xl border-2 p-3 flex flex-col items-center gap-2 text-center transition-all ${
                      !c.supporte
                        ? "border-gray-100 bg-gray-50 text-gray-300 cursor-not-allowed opacity-50"
                        : chassisNom === c.nom
                        ? "border-janneau-teal bg-janneau-teal-light text-janneau-teal-dark"
                        : "border-gray-200 bg-white text-gray-600 hover:border-janneau-teal/40 hover:shadow-sm"
                    }`}
                  >
                    <span className={chassisNom === c.nom ? "text-janneau-teal" : "text-gray-300"}>
                      <WindowDiagram />
                    </span>
                    <span className="text-[11px] font-medium leading-tight">{c.nom}</span>
                    {!c.supporte && <span className="text-[9px] text-amber-500">Bientôt disponible</span>}
                  </button>
                ))}
              </div>
            )}
          </StepSection>

          {/* ── STEPS 3 & 4 — Dimensions ─────────────────────────────────── */}
          <StepSection number={3} title="Dimensions de la menuiserie" active={step3Active}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <NumberInput
                  label="Largeur (dos de profil)"
                  value={largeur}
                  onChange={setLargeur}
                  min={100}
                  max={4000}
                  unit="mm"
                  required
                />
                <p className="text-xs text-gray-400 mt-1">Ex : 1200 mm pour une fenêtre standard</p>
              </div>
              <div>
                <NumberInput
                  label="Hauteur (dos de profil)"
                  value={hauteur}
                  onChange={setHauteur}
                  min={100}
                  max={3000}
                  unit="mm"
                  required
                />
                <p className="text-xs text-gray-400 mt-1">Ex : 1350 mm pour une fenêtre standard</p>
              </div>
            </div>
          </StepSection>

          {/* ── STEP 4 — Couleur extérieure ──────────────────────────────── */}
          <StepSection number={4} title="Couleur extérieure" active={step4Active}>
            {/* Couleur sélectionnée */}
            {couleur && (
              <div className="flex items-center gap-3 mb-5 p-3 bg-gray-50 rounded-xl border border-gray-200">
                <span
                  className="w-10 h-10 rounded-lg border border-gray-200 flex-shrink-0 shadow-inner"
                  style={{ backgroundColor: selectedCouleurHex ?? "#ccc" }}
                />
                <div>
                  <div className="text-sm font-semibold text-gray-800">{couleur}</div>
                  <div className="text-xs text-gray-400">Couleur sélectionnée</div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-2">
              {couleurs.map((c) => {
                const hex = colorHex(c.nom);
                const light = isLight(hex);
                const selected = couleur === c.nom;
                return (
                  <button
                    key={c.nom}
                    type="button"
                    title={c.nom}
                    onClick={() => setCouleur(c.nom)}
                    className={`group flex flex-col items-center gap-1.5 p-1.5 rounded-xl transition-all ${
                      selected ? "ring-2 ring-janneau-teal ring-offset-2 scale-105" : "hover:scale-105"
                    }`}
                  >
                    <span
                      className="w-10 h-10 rounded-lg border border-gray-200 shadow-sm relative flex items-center justify-center"
                      style={{ backgroundColor: hex }}
                    >
                      {selected && (
                        <svg className={`w-5 h-5 ${light ? "text-gray-700" : "text-white"}`} viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" />
                        </svg>
                      )}
                    </span>
                    <span className="text-[9px] text-gray-500 leading-tight text-center max-w-[48px] truncate group-hover:text-janneau-teal">
                      {c.nom.replace(/\s*-\s*RAL\s*\d{4}/i, "").replace(/\s*-\s*Ral\s*\d{4}/i, "")}
                    </span>
                  </button>
                );
              })}
            </div>
          </StepSection>

          {/* ── STEP 5 — Remplissage vitrage ─────────────────────────────── */}
          <StepSection number={5} title="Remplissage vitrage" active={step5Active}>
            <p className="text-xs text-gray-400 mb-4">
              Laissez vide pour utiliser les valeurs par défaut (Ug 1.1 W/(m²·K), Sg 0.65, Tlg 82 %).
            </p>

            <div className="space-y-3">
              {vitragInputs.map((v, i) => (
                <VitrageRow
                  key={v.zone}
                  label={`Vitrage ${i + 1}`}
                  zone={v.zone}
                  value={v}
                  onChange={(updated) =>
                    setVitragInputs((prev) => prev.map((x, j) => (j === i ? updated : x)))
                  }
                  vitrages={vitrages}
                  intercalaires={intercalaires}
                />
              ))}
              {isPorte &&
                panneauInputs.map((p, i) => (
                  <VitrageRow
                    key={p.zone}
                    label={`Panneau ${i + 1}`}
                    zone={p.zone}
                    value={p}
                    onChange={(updated) =>
                      setPanneauInputs((prev) => prev.map((x, j) => (j === i ? updated : x)))
                    }
                    vitrages={vitrages}
                    intercalaires={intercalaires}
                  />
                ))}
              {vitragInputs.length === 0 && (
                <button
                  type="button"
                  onClick={() => setVitragInputs([makeVitrag("G1")])}
                  className="text-sm text-janneau-teal hover:underline"
                >
                  + Ajouter un vitrage
                </button>
              )}
            </div>
          </StepSection>

          {/* ── STEP 6 — Volet roulant ───────────────────────────────────── */}
          <StepSection number={6} title="Volet roulant (optionnel)" active={step6Active}>
            <label className="flex items-center gap-3 cursor-pointer select-none">
              <div
                onClick={() => setVoletInput((v) => ({ ...v, actif: !v.actif }))}
                className={`w-11 h-6 rounded-full transition-colors cursor-pointer flex-shrink-0 ${
                  voletInput.actif ? "bg-janneau-teal" : "bg-gray-300"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white shadow mt-0.5 transition-transform ${
                    voletInput.actif ? "translate-x-5 ml-0.5" : "translate-x-0.5"
                  }`}
                />
              </div>
              <span className="text-sm text-gray-700 font-medium">Avec volet roulant</span>
            </label>

            {voletInput.actif && (
              <div className="mt-4 grid sm:grid-cols-2 gap-4">
                <Select
                  label="Type de volet"
                  value={voletInput.type ?? ""}
                  onChange={(v) => setVoletInput((prev) => ({ ...prev, type: v || null }))}
                  options={volets.map((v) => ({ value: v.designation, label: v.designation }))}
                  required
                />
                <Select
                  label="Isolation acoustique coffre"
                  value={voletInput.isolation_acoustique}
                  onChange={(v) => setVoletInput((prev) => ({ ...prev, isolation_acoustique: v }))}
                  options={
                    selectedVolet
                      ? selectedVolet.isolations_disponibles.map((i) => {
                          const found = ISOLATION_OPTIONS.find((o) => o.value === i);
                          return found ?? { value: i, label: i };
                        })
                      : ISOLATION_OPTIONS
                  }
                />
              </div>
            )}
          </StepSection>

          {/* ── CTA ─────────────────────────────────────────────────────────── */}
          <button
            type="submit"
            disabled={!canSubmit || loading}
            className="w-full bg-janneau-teal hover:bg-janneau-teal-dark text-white font-semibold py-4 rounded-2xl text-base tracking-wide shadow-lg disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-xl"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Calcul en cours…
              </span>
            ) : (
              "Calculer les performances thermiques"
            )}
          </button>
        </form>

        {/* ── STEP 7 — Résultats ───────────────────────────────────────────── */}
        <div ref={resultRef}>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-sm text-red-700 flex gap-3">
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-4.75a.75.75 0 001.5 0V8.75a.75.75 0 00-1.5 0v4.5zm.75-6a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
              </svg>
              <div><strong>Erreur :</strong> {error}</div>
            </div>
          )}

          {result && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold bg-janneau-teal text-white">
                  7
                </span>
                <h2 className="font-semibold text-base uppercase tracking-wide text-janneau-teal-dark">
                  Résultats
                </h2>
              </div>
              <ResultCard
                result={result}
                recapChassis={chassisNom}
                recapLargeur={typeof largeur === "number" ? largeur : 0}
                recapHauteur={typeof hauteur === "number" ? hauteur : 0}
                recapCouleur={couleur}
                recapCouleurHex={selectedCouleurHex ?? "#ccc"}
              />
            </div>
          )}
        </div>

        {/* Normes */}
        <div className="text-center text-xs text-gray-300 space-y-0.5 pb-4">
          <div>EN ISO 10077-1 (juin 2012) · XP P50-777 (décembre 2011) · EN ISO 6946:2017</div>
          <div>© JANNEAU Menuisier Créateur — Outil réservé aux professionnels</div>
        </div>
      </div>
    </div>
  );
}
