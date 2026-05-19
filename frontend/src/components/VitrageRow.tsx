import type { VitragInput, VitrageOption } from "../types";
import { Select } from "./Select";

interface VitrageRowProps {
  label: string;
  zone: string;
  value: VitragInput;
  onChange: (v: VitragInput) => void;
  vitrages: VitrageOption[];
  intercalaires: string[];
  accentColor?: "blue" | "amber";
  hideIntercalaire?: boolean;
}

const ACCENT = {
  blue:  { border: "border-blue-200",  text: "text-blue-700" },
  amber: { border: "border-amber-300", text: "text-amber-700" },
} as const;

export function VitrageRow({ label, zone, value, onChange, vitrages, intercalaires, accentColor = "blue", hideIntercalaire }: VitrageRowProps) {
  const compositionOptions = vitrages.map((v) => ({
    value: v.composition,
    label: `${v.composition} (Ug ${v.Ug})`,
  }));
  const intercalaireOptions = intercalaires.map((i) => ({ value: i, label: i }));
  const accent = ACCENT[accentColor];

  return (
    <div className={`grid grid-cols-2 gap-3 items-end border-l-2 ${accent.border} pl-3`}>
      <div className={`col-span-2 text-sm font-semibold ${accent.text}`}>{label} ({zone})</div>
      <div className={hideIntercalaire ? "col-span-2" : ""}>
        <Select
          label="Composition"
          value={value.composition}
          onChange={(v) => onChange({ ...value, zone, composition: v })}
          options={compositionOptions}
          required
        />
      </div>
      {!hideIntercalaire && (
        <Select
          label="Intercalaire"
          value={value.intercalaire}
          onChange={(v) => onChange({ ...value, zone, intercalaire: v })}
          options={intercalaireOptions}
        />
      )}
    </div>
  );
}
