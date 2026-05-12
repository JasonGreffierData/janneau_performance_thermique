export interface ChassisInfo {
  id: number;
  nom: string;
  famille: string;
  gamme_code: string;
  supporte: boolean;
}

export interface VitrageOption {
  composition: string;
  Ug: number;
  type: string;
}

export interface CouleurOption {
  nom: string;
  alpha: number;
  famille_prix?: string;
}

export interface VoletOption {
  designation: string;
  rR: number;
  hauteur_coffre: number;
  gammes_compatibles: string[];
  isolations_disponibles: string[];
}

export interface VitragInput {
  zone: string;
  composition: string;
  intercalaire: string;
}

export interface VoletInput {
  actif: boolean;
  type: string | null;
  isolation_acoustique: string;
}

export interface CalculInput {
  famille: string;
  chassis: string;
  couleur: string;
  hauteur_mm: number;
  largeur_mm: number;
  volet: VoletInput;
  vitrages: VitragInput[];
  panneaux: VitragInput[];
}

export interface ResultatMenuiserie {
  Uw: number | null;
  Sw: number | null;
  Tlw: number | null;
  label_uw: string;
}

export interface ResultatVolet {
  rR: number | null;
  Ujn: number | null;
  Ubb_jn: number | null;
  Uc: number | null;
}

export interface DetailsCalcul {
  chassis_id: number;
  geo_type: string;
  Uf_moyen: number | null;
  Af_total: number | null;
  Ag_total: number | null;
  surface_totale: number | null;
  normes: string[];
}

export interface CalculResult {
  menuiserie_seule: ResultatMenuiserie;
  avec_volet: ResultatVolet | null;
  details: DetailsCalcul;
}
