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
import { colorHex } from "./utils/ralColors";

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

// Mise en forme lisible du nom de famille (MAJUSCULES → Titre)
function familleShortLabel(f: string): string {
  return f.toLowerCase().replace(/(?:^|\s|'|-)\S/g, (c) => c.toUpperCase());
}

function makeVitrag(zone: string): VitragInput {
  return { zone, composition: "", intercalaire: DEFAULT_INTERCALAIRE };
}

// Petit séparateur de section dans le formulaire
function FormSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">{label}</p>
      {children}
    </div>
  );
}

// Placeholder colonne droite quand pas encore de résultats
function EmptyResults() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8 gap-4">
      <div className="grid grid-cols-3 gap-3 w-full max-w-sm">
        {[
          { code: "Uw", label: "Transmission thermique", unit: "W/(m²·K)" },
          { code: "Sw", label: "Facteur solaire", unit: "0 à 1" },
          { code: "TLw", label: "Transmission lumineuse", unit: "%" },
        ].map((m) => (
          <div key={m.code} className="bg-white border border-gray-200 rounded-2xl p-4 flex flex-col items-center gap-1">
            <span className="text-2xl font-bold text-gray-200">—</span>
            <span className="text-xs text-gray-300">{m.unit}</span>
            <span className="text-xs font-semibold text-gray-300 mt-1">{m.code}</span>
            <span className="text-[10px] text-gray-200 leading-tight">{m.label}</span>
          </div>
        ))}
      </div>
      <p className="text-sm text-gray-300 max-w-xs">
        Renseignez les paramètres à gauche et cliquez sur <strong className="text-gray-400">Calculer</strong> pour obtenir les résultats.
      </p>
    </div>
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

  const allVitrages = useVitrages();
  const vitrages = allVitrages.filter((v) => v.type !== "PANNEAUX");
  const panneauxOptions = allVitrages.filter((v) => v.type === "PANNEAUX");
  const intercalaires = useIntercalaires();
  const couleurs = useCouleurs();
  const volets = useVolets(selectedChassis?.gamme_code);

  const [couleur, setCouleur] = useState("");
  const [hauteur, setHauteur] = useState<number | "">("");
  const [largeur, setLargeur] = useState<number | "">("");

  const [hauteurSoubassement, setHauteurSoubassement] = useState<number | "">(450);

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

  function handleFamilleChange(f: string) {
    setFamille(f);
    setChassisNom("");
    setResult(null);
  }

  function handleChassisChange(nom: string) {
    setChassisNom(nom);
    setResult(null);
    const ch = chassisList.find((c) => c.nom === nom);
    if (!ch) { setVitragInputs([]); setPanneauInputs([]); return; }
    const nbV = ch.nb_vitrages || 1;
    const nbP = ch.nb_panneaux || 0;
    setVitragInputs(Array.from({ length: nbV }, (_, i) => makeVitrag(`G${i + 1}`)));
    setPanneauInputs(Array.from({ length: nbP }, (_, i) => makeVitrag(`P${i + 1}`)));
    setHauteurSoubassement(450);
  }

  function syncZones(res: CalculResult) {
    const nbV = selectedChassis?.nb_vitrages ?? (res.details.zones_vitrage.filter((z) => z.zone.startsWith("G")).length || 1);
    const nbP = selectedChassis?.nb_panneaux ?? res.details.zones_vitrage.filter((z) => z.zone.startsWith("P")).length;
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
        ...(panneauInputs.length > 0 && typeof hauteurSoubassement === "number"
          ? { hauteur_soubassement_mm: hauteurSoubassement }
          : {}),
      });
      setResult(res);
      syncZones(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  const selectedVolet = volets.find((v) => v.designation === voletInput.type);
  const selectedCouleurHex = couleur ? colorHex(couleur) : null;

  const canSubmit =
    !!famille &&
    !!chassisNom &&
    selectedChassis?.supporte !== false &&
    !!couleur &&
    !!hauteur &&
    !!largeur;

  return (
    <div className="h-screen flex flex-col bg-gray-50 font-sans overflow-hidden">

      {/* ── HEADER ────────────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 bg-janneau-dark text-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img src="/logo-janneau.png" alt="Janneau" className="h-8 w-auto brightness-0 invert" />
          <div className="hidden sm:block border-l border-white/20 pl-4">
            <p className="text-xs font-semibold text-janneau-teal uppercase tracking-widest">Outil Pro</p>
            <p className="text-sm font-bold leading-tight">Calculateur Thermo-luminosité<sup className="text-[10px]">®</sup></p>
          </div>
        </div>
        <div className="text-[10px] text-gray-400 uppercase tracking-widest hidden md:block">
          EN ISO 10077-1 · XP P50-777
        </div>
      </header>

      {/* ── MAIN : deux colonnes ──────────────────────────────────────────── */}
      <div className="flex-1 grid grid-cols-[2fr_3fr] overflow-hidden">

        {/* ── COLONNE GAUCHE : formulaire ─────────────────────────────────── */}
        <div className="overflow-y-auto bg-white border-r border-gray-200 flex flex-col">
          <form onSubmit={handleCalculer} className="flex flex-col gap-4 p-5 flex-1">

            {/* Famille */}
            <FormSection label="Famille de produit">
              <div className="flex flex-wrap gap-1.5">
                {familles.map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => handleFamilleChange(f)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      famille === f
                        ? "bg-janneau-teal text-white border-janneau-teal"
                        : "bg-white text-gray-600 border-gray-200 hover:border-janneau-teal/50"
                    }`}
                  >
                    {familleShortLabel(f)}
                  </button>
                ))}
              </div>
            </FormSection>

            {/* Châssis */}
            <FormSection label="Type de châssis">
              <Select
                label=""
                value={chassisNom}
                onChange={handleChassisChange}
                disabled={!famille}
                options={chassisList
                  .filter((c) => c.supporte)
                  .map((c) => ({ value: c.nom, label: c.nom }))}
              />
            </FormSection>

            {/* Dimensions */}
            <FormSection label="Dimensions (mm)">
              <div className="grid grid-cols-2 gap-3">
                <NumberInput label="Largeur" value={largeur} onChange={setLargeur} min={100} max={4000} unit="mm" />
                <NumberInput label="Hauteur" value={hauteur} onChange={setHauteur} min={100} max={3000} unit="mm" />
              </div>
            </FormSection>

            {/* Hauteur soubassement */}
            {panneauInputs.length > 0 && (
              <FormSection label="Hauteur soubassement (mm)">
                <NumberInput
                  label="Hauteur panneau"
                  value={hauteurSoubassement}
                  onChange={setHauteurSoubassement}
                  min={100}
                  max={1500}
                  unit="mm"
                />
                <p className="text-[10px] text-gray-400">Hauteur de la partie basse opaque. Défaut : 450 mm.</p>
              </FormSection>
            )}

            {/* Couleur */}
            <FormSection label="Couleur extérieure">
              <div className="flex items-center gap-2">
                {selectedCouleurHex && (
                  <span className="w-8 h-8 rounded-md border border-gray-200 flex-shrink-0 shadow-sm" style={{ backgroundColor: selectedCouleurHex }} />
                )}
                <div className="flex-1">
                  <Select
                    label=""
                    value={couleur}
                    onChange={setCouleur}
                    disabled={!chassisNom}
                    options={couleurs.map((c) => ({ value: c.nom, label: c.nom }))}
                  />
                </div>
              </div>
            </FormSection>

            {/* Vitrage */}
            {vitragInputs.length > 0 && (
              <FormSection label="Remplissage vitrage">
                <p className="text-[10px] text-gray-400">Vide = valeurs par défaut (Ug 1,1 · Sg 0,65 · Tlg 82%)</p>
                <div className="space-y-2">
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
                </div>
              </FormSection>
            )}

            {/* Panneaux */}
            {panneauInputs.length > 0 && (
              <FormSection label="Remplissage panneaux">
                <p className="text-[10px] text-gray-400">Vide = valeurs par défaut (Ug 2,4 · Sg 0 · Tlg 0%)</p>
                <div className="space-y-2">
                  {panneauInputs.map((p, i) => (
                    <VitrageRow
                      key={p.zone}
                      label={`Panneau ${i + 1}`}
                      zone={p.zone}
                      value={p}
                      onChange={(updated) =>
                        setPanneauInputs((prev) => prev.map((x, j) => (j === i ? updated : x)))
                      }
                      vitrages={panneauxOptions}
                      intercalaires={intercalaires}
                      accentColor="amber"
                      hideIntercalaire
                    />
                  ))}
                </div>
              </FormSection>
            )}

            {/* Volet */}
            <FormSection label="Volet roulant (optionnel)">
              <div
                onClick={() => setVoletInput((v) => ({ ...v, actif: !v.actif }))}
                className="flex items-center gap-2 cursor-pointer w-fit"
              >
                <div className={`w-9 h-5 rounded-full transition-colors flex-shrink-0 ${voletInput.actif ? "bg-janneau-teal" : "bg-gray-300"}`}>
                  <div className={`w-4 h-4 rounded-full bg-white shadow mt-0.5 transition-transform ${voletInput.actif ? "translate-x-4 ml-0.5" : "translate-x-0.5"}`} />
                </div>
                <span className="text-xs text-gray-700 font-medium select-none">Avec volet roulant</span>
              </div>
              {voletInput.actif && (
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <Select
                    label="Type de volet"
                    value={voletInput.type ?? ""}
                    onChange={(v) => setVoletInput((prev) => ({ ...prev, type: v || null }))}
                    options={volets.map((v) => ({ value: v.designation, label: v.designation }))}
                  />
                  <Select
                    label="Isolation coffre"
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
            </FormSection>

            {/* CTA */}
            <div className="mt-auto pt-2">
              <button
                type="submit"
                disabled={!canSubmit || loading}
                className="w-full bg-janneau-teal hover:bg-janneau-teal-dark text-white font-semibold py-3 rounded-xl text-sm tracking-wide shadow disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Calcul en cours…
                  </span>
                ) : "Calculer les performances thermiques"}
              </button>
            </div>

          </form>
        </div>

        {/* ── COLONNE DROITE : résultats ──────────────────────────────────── */}
        <div ref={resultRef} className="overflow-y-auto bg-gray-50 p-5">
          {!result && !error && <EmptyResults />}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-red-700 flex gap-3">
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-4.75a.75.75 0 001.5 0V8.75a.75.75 0 00-1.5 0v4.5zm.75-6a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
              </svg>
              <div><strong>Erreur :</strong> {error}</div>
            </div>
          )}

          {result && (
            <ResultCard
              result={result}
              recapFamille={famille}
              recapChassis={chassisNom}
              recapLargeur={typeof largeur === "number" ? largeur : 0}
              recapHauteur={typeof hauteur === "number" ? hauteur : 0}
              recapCouleur={couleur}
              recapCouleurHex={selectedCouleurHex ?? "#ccc"}
            />
          )}

          <div className="text-center text-[10px] text-gray-300 mt-6 space-y-0.5">
            <div>EN ISO 10077-1 · XP P50-777 · EN ISO 6946:2017</div>
            <div>© JANNEAU Menuisier Créateur — Outil réservé aux professionnels</div>
          </div>
        </div>

      </div>
    </div>
  );
}
