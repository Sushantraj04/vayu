export interface AqiCategoryInfo {
  name: string;
  hindiName: string;
  minC: number;
  maxC: number;
  minI: number;
  maxI: number;
  color: string;
  textColor: string;
  bgLight: string;
  severity: 'low' | 'moderate' | 'elevated' | 'high' | 'critical' | 'emergency';
  advisoryEn: string;
  advisoryHi: string;
}

export const CPCB_AQI_CATEGORIES: AqiCategoryInfo[] = [
  {
    name: "Good",
    hindiName: "अच्छा",
    minC: 0.0,
    maxC: 30.0,
    minI: 0,
    maxI: 50,
    color: "#16a34a",
    textColor: "#ffffff",
    bgLight: "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800",
    severity: "low",
    advisoryEn: "Air quality is good. Enjoy outdoor activities.",
    advisoryHi: "हवा की गुणवत्ता अच्छी है। बाहरी गतिविधियों का आनंद लें।"
  },
  {
    name: "Satisfactory",
    hindiName: "संतोषजनक",
    minC: 31.0,
    maxC: 60.0,
    minI: 51,
    maxI: 100,
    color: "#65a30d",
    textColor: "#ffffff",
    bgLight: "bg-lime-50 text-lime-800 dark:bg-lime-950/50 dark:text-lime-300 border-lime-300 dark:border-lime-800",
    severity: "moderate",
    advisoryEn: "Minor breathing discomfort to sensitive people.",
    advisoryHi: "संवेदनशील लोगों को सांस लेने में हल्की परेशानी हो सकती है।"
  },
  {
    name: "Moderate",
    hindiName: "मध्यम",
    minC: 61.0,
    maxC: 90.0,
    minI: 101,
    maxI: 200,
    color: "#d97706",
    textColor: "#ffffff",
    bgLight: "bg-amber-50 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 border-amber-300 dark:border-amber-800",
    severity: "elevated",
    advisoryEn: "Breathing discomfort to asthmatics and sensitive groups.",
    advisoryHi: "अस्थमा और फेफड़ों के रोगियों को सांस लेने में परेशानी हो सकती है।"
  },
  {
    name: "Poor",
    hindiName: "खराब",
    minC: 91.0,
    maxC: 120.0,
    minI: 201,
    maxI: 300,
    color: "#ea580c",
    textColor: "#ffffff",
    bgLight: "bg-orange-50 text-orange-800 dark:bg-orange-950/50 dark:text-orange-300 border-orange-300 dark:border-orange-800",
    severity: "high",
    advisoryEn: "Breathing discomfort on prolonged exposure. Wear N95 outdoors.",
    advisoryHi: "लंबे समय तक संपर्क से सांस की तकलीफ हो सकती है। N95 मास्क पहनें।"
  },
  {
    name: "Very Poor",
    hindiName: "बहुत खराब",
    minC: 121.0,
    maxC: 250.0,
    minI: 301,
    maxI: 400,
    color: "#dc2626",
    textColor: "#ffffff",
    bgLight: "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-300 border-red-300 dark:border-red-800",
    severity: "critical",
    advisoryEn: "Respiratory illness risk. Avoid prolonged outdoor exertion.",
    advisoryHi: "सांस की बीमारी का खतरा। लंबे समय तक बाहर रहने से बचें।"
  },
  {
    name: "Severe",
    hindiName: "गंभीर",
    minC: 251.0,
    maxC: 500.0,
    minI: 401,
    maxI: 500,
    color: "#7f1d1d",
    textColor: "#ffffff",
    bgLight: "bg-rose-50 text-rose-950 dark:bg-rose-950/70 dark:text-rose-200 border-rose-400 dark:border-rose-900",
    severity: "emergency",
    advisoryEn: "Health emergency! Severe impact on everyone. Stay indoors.",
    advisoryHi: "स्वास्थ्य आपातकाल! सभी पर गंभीर प्रभाव। घर के अंदर रहें।"
  }
];

export function getAqiCategory(aqiValue: number | null | undefined): AqiCategoryInfo | null {
  if (aqiValue === null || aqiValue === undefined || isNaN(aqiValue)) return null;
  if (aqiValue <= 50) return CPCB_AQI_CATEGORIES[0];
  if (aqiValue <= 100) return CPCB_AQI_CATEGORIES[1];
  if (aqiValue <= 200) return CPCB_AQI_CATEGORIES[2];
  if (aqiValue <= 300) return CPCB_AQI_CATEGORIES[3];
  if (aqiValue <= 400) return CPCB_AQI_CATEGORIES[4];
  return CPCB_AQI_CATEGORIES[5];
}

export function getAqiColor(aqiValue: number | null | undefined): string {
  const cat = getAqiCategory(aqiValue);
  return cat ? cat.color : '#64748b';
}

export function calculateAqiFromPm25(pm25: number | null | undefined): { aqi: number; category: AqiCategoryInfo } | null {
  if (pm25 === null || pm25 === undefined || isNaN(pm25) || pm25 < 0) return null;
  
  let target = CPCB_AQI_CATEGORIES[5];
  for (const cat of CPCB_AQI_CATEGORIES) {
    if (pm25 <= cat.maxC) {
      target = cat;
      break;
    }
  }

  const factor = (target.maxI - target.minI) / (target.maxC - target.minC);
  const aqi = Math.round(target.minI + factor * (pm25 - target.minC));
  return { aqi: Math.min(500, Math.max(0, aqi)), category: target };
}
