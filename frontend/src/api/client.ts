import type {
  CalculInput,
  CalculResult,
  ChassisInfo,
  CouleurOption,
  VitrageOption,
  VoletOption,
} from "../types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail: string }).detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getFamilles: () => get<string[]>("/familles"),
  getChassis: (famille?: string) =>
    get<ChassisInfo[]>(`/chassis${famille ? `?famille=${encodeURIComponent(famille)}` : ""}`),
  getVitrages: (type?: string) =>
    get<VitrageOption[]>(`/vitrages${type ? `?type_vitrage=${encodeURIComponent(type)}` : ""}`),
  getIntercalaires: () => get<string[]>("/intercalaires"),
  getCouleurs: () => get<CouleurOption[]>("/couleurs"),
  getVolets: (gamme_code?: string) =>
    get<VoletOption[]>(`/volets${gamme_code ? `?gamme_code=${encodeURIComponent(gamme_code)}` : ""}`),
  calculer: (inp: CalculInput) => post<CalculResult>("/calculer", inp),
};
