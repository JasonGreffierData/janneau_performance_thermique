import type { VitragInput, VitrageOption } from "../types";
import { Select } from "./Select";

interface VitrageRowProps {
  label: string;
  zone: string;
  value: VitragInput;
  onChange: (v: VitragInput) => void;
  vitrages: VitrageOption[];
  intercalaires: string[];
}

export function VitrageRow({ label, zone, value, onChange, vitrages, intercalaires }: VitrageRowProps) {
  const compositionOptions = vitrages.map((v) => ({
    value: v.composition,
    label: `${v.composition} (Ug ${v.Ug})`,
  }));
  const intercalaireOptions = intercalaires.map((i) => ({ value: i, label: i }));

  return (
    <div className="grid grid-cols-2 gap-3 items-end border-l-2 border-blue-200 pl-3">
      <div className="col-span-2 text-sm font-semibold text-blue-700">{label} ({zone})</div>
      <Select
        label="Composition"
        value={value.composition}
        onChange={(v) => onChange({ ...value, zone, composition: v })}
        options={compositionOptions}
        required
      />
      <Select
        label="Intercalaire"
        value={value.intercalaire}
        onChange={(v) => onChange({ ...value, zone, intercalaire: v })}
        options={intercalaireOptions}
      />
    </div>
  );
}
