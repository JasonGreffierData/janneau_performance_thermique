/**
 * Correspondance RAL → hex pour l'affichage des swatches de couleur.
 * Complété par des noms courants Janneau sans code RAL.
 */

const RAL_HEX: Record<string, string> = {
  "1015": "#E6D2AE",
  "3002": "#8B1A1A",
  "3004": "#6B1720",
  "3005": "#5B1B1F",
  "3081": "#6B1F1F",
  "5003": "#1B294B",
  "5007": "#3D5F7E",
  "5010": "#0E4E8A",
  "5011": "#232C3F",
  "5023": "#5C7E92",
  "6005": "#2B5733",
  "6021": "#87A878",
  "7001": "#8C96A0",
  "7006": "#766A5A",
  "7016": "#383E42",
  "7021": "#2B2B2C",
  "7022": "#47403B",
  "7024": "#474A50",
  "7035": "#D7D7D7",
  "7038": "#B5B5A3",
  "7047": "#D0D0CE",
  "8007": "#7B4B1C",
  "8014": "#4A3525",
  "8017": "#442B22",
  "8019": "#3A3228",
  "8028": "#4E3527",
  "8518": "#3B2A20",
  "8875": "#5C3D28",
  "9001": "#FDF4DA",
  "9002": "#E7E7E0",
  "9005": "#0E0E10",
  "9006": "#A5A5A5",
  "9007": "#8F8F8C",
  "9010": "#F4F4F4",
  "9016": "#F6F6F6",
};

const NAME_HEX: Record<string, string> = {
  "acajou":                     "#5C2D1E",
  "anteak":                     "#8B6914",
  "chêne clair irlandais":      "#C9A96E",
  "chêne doré":                 "#B5872E",
  "noyer":                      "#6B4226",
  "silice":                     "#C8C0B0",
  "platine":                    "#D8D4CC",
  "argent":                     "#C0C0C0",
  "ivoire":                     "#FFFFF0",
  "ivoire 100":                 "#F5F0DC",
  "ivoire clair":               "#E6D2AE",
  "bronze 1247":                "#7B5C3A",
  "anthracite foncé":           "#2B2B2B",
  "anthracite stylo":           "#3A3A3A",
  "gris as1":                   "#7A7A7A",
  "gris 2800":                  "#6A6A6A",
  "gris 2900":                  "#4A4A4A",
  "gris basalte":               "#5A5855",
  "gris quartz":                "#8B8B88",
  "gris galet 9660mb":          "#9A9590",
  "gris satiné effet nacré 9006sn": "#ADADAD",
  "brun foncé":                 "#3B2A1A",
  "anodic ice":                 "#E8F4F8",
  "anodic champagne":           "#D4C09A",
  "bleu canon":                 "#1A2B3C",
  "rouille mars":               "#8B4513",
  "noir 2100":                  "#1A1A1A",
  "rouge 2100":                 "#C0392B",
  "bleu 2700":                  "#2C5F8A",
  "impression blanche":         "#FFFFFF",
  "ifh":                        "#FFFFFF",
  "blanc crème":                "#FDF4DA",
  "blanc trafic":               "#F6F6F6",
  "blanc pur":                  "#F4F4F4",
};

/** Extrait le code RAL depuis un nom de couleur, ex: "Gris anthracite - RAL 7016" → "7016" */
function extractRalCode(nom: string): string | null {
  const match = nom.match(/ral\s*(\d{4})/i);
  return match ? match[1] : null;
}

/** Retourne la couleur hex pour un nom de couleur Janneau. */
export function colorHex(nom: string): string {
  const ralCode = extractRalCode(nom);
  if (ralCode && RAL_HEX[ralCode]) return RAL_HEX[ralCode];

  const key = nom.toLowerCase().replace(/\s*-\s*ral\s*\d{4}/i, "").trim();
  return NAME_HEX[key] ?? "#CCCCCC";
}
