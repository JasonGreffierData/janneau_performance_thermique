import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  ChassisInfo,
  CouleurOption,
  VitrageOption,
  VoletOption,
} from "../types";

export function useFamilles() {
  const [familles, setFamilles] = useState<string[]>([]);
  useEffect(() => {
    api.getFamilles().then(setFamilles).catch(console.error);
  }, []);
  return familles;
}

export function useChassis(famille: string | null) {
  const [chassis, setChassis] = useState<ChassisInfo[]>([]);
  useEffect(() => {
    if (!famille) { setChassis([]); return; }
    api.getChassis(famille).then(setChassis).catch(console.error);
  }, [famille]);
  return chassis;
}

export function useVitrages() {
  const [vitrages, setVitrages] = useState<VitrageOption[]>([]);
  useEffect(() => {
    api.getVitrages().then(setVitrages).catch(console.error);
  }, []);
  return vitrages;
}

export function useIntercalaires() {
  const [intercalaires, setIntercalaires] = useState<string[]>([]);
  useEffect(() => {
    api.getIntercalaires().then(setIntercalaires).catch(console.error);
  }, []);
  return intercalaires;
}

export function useCouleurs() {
  const [couleurs, setCouleurs] = useState<CouleurOption[]>([]);
  useEffect(() => {
    api.getCouleurs().then((all) => {
      // Dédupliquer par code RAL si présent, sinon par nom normalisé (minuscule)
      // Évite les doublons dus aux variations de casse ("RAL 3004" vs "Ral 3004")
      const seen = new Set<string>();
      const dedupKey = (nom: string) => {
        const m = nom.match(/\d{4,5}/);
        return m ? `RAL-${m[0]}` : nom.toLowerCase().trim();
      };
      const dedup = all.filter((c) => {
        const key = dedupKey(c.nom);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      dedup.sort((a, b) => a.nom.localeCompare(b.nom, "fr", { sensitivity: "base" }));
      setCouleurs(dedup);
    }).catch(console.error);
  }, []);
  return couleurs;
}

export function useVolets(gamme_code?: string) {
  const [volets, setVolets] = useState<VoletOption[]>([]);
  useEffect(() => {
    api.getVolets(gamme_code).then(setVolets).catch(console.error);
  }, [gamme_code]);
  return volets;
}
