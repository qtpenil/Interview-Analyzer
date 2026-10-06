// Centralized theme tokens for the InteReview landing site.
//
// Each theme defines semantic CSS custom properties. The ThemeProvider
// writes these values onto `document.documentElement` so every component
// can read them via Tailwind's var() utilities (e.g. `bg-background`,
// `text-primary`, `border-default`). This keeps colors out of component code
// and lets the entire UI re-theme from a single source of truth.

export type ThemeName = "dark" | "light";

export type ThemeTokens = {
  /* Base surfaces */
  background: string; // page background
  surface: string; // cards, panels
  surfaceHover: string; // hover state for surfaces
  elevated: string; // elevated menus, popovers
  card: string; // card background
  border: string; // default border
  borderStrong: string; // emphasized border

  /* Text */
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textInverse: string; // text on accent fills

  /* Accent / brand */
  accent: string;
  accentSoft: string; // translucent accent (rgba)
  accentSoftBorder: string;

  /* Buttons */
  btnPrimaryFrom: string;
  btnPrimaryTo: string;
  btnPrimaryText: string;
  btnSecondaryBg: string;
  btnSecondaryBorder: string;
  btnSecondaryText: string;

  /* Inputs */
  inputBg: string;
  inputBorder: string;
  inputText: string;
  inputPlaceholder: string;

  /* Effects */
  shadow: string;
  shadowGlow: string;
  ring: string; // focus ring color (rgba)

  /* shadcn compat aliases */
  popover: string;
  popoverForeground: string;
  foreground: string;
  mutedForeground: string;
  accentForeground: string;

  /* Gradients */
  gradientStart: string;
  gradientEnd: string;
  gradientHero: string; // background gradient for hero/sections
  gradientRadial: string; // radial glow overlay

  /* Status (semantic, shared language across themes) */
  success: string;
  successSoft: string;
  successBorder: string;
  warning: string;
  warningSoft: string;
  warningBorder: string;
  danger: string;
  dangerSoft: string;
  dangerBorder: string;
  info: string;
  infoSoft: string;
  infoBorder: string;
};

// Night theme — monochromatic black & grey, borderless.
//
// Surface ladder (page -> panel -> card -> menu -> hover):
//   #000000 -> #0A0A0A -> #111111 -> #181818 -> #1A1A1A
// Borders are fully transparent — hierarchy is carried purely by surface
// fills. Typography steps down from off-white (#F5F5F5) through grey
// (#B3B3B3, #808080). The accent is a mid grey used for focus borders and
// highlights; status colors keep their semantic hues.
export const darkTheme: ThemeTokens = {
  background: "#000000",
  surface: "#0A0A0A",
  surfaceHover: "#1A1A1A",
  elevated: "#181818",
  card: "#111111",
  border: "transparent",
  borderStrong: "transparent",

  textPrimary: "#F5F5F5",
  textSecondary: "#B3B3B3",
  textMuted: "#808080",
  textInverse: "#0A0A0A",

  accent: "#555555",
  accentSoft: "rgba(255, 255, 255, 0.07)",
  accentSoftBorder: "transparent",

  btnPrimaryFrom: "#DADADA",
  btnPrimaryTo: "#F5F5F5",
  btnPrimaryText: "#0A0A0A",
  btnSecondaryBg: "#181818",
  btnSecondaryBorder: "transparent",
  btnSecondaryText: "#F5F5F5",

  inputBg: "#181818",
  inputBorder: "transparent",
  inputText: "#F5F5F5",
  inputPlaceholder: "#707070",

  shadow:
    "0 4px 8px rgba(255, 255, 255, 0.08), 0 6px 12px rgba(255, 255, 255, 0.05)",
  shadowGlow: "0 0 32px -12px rgba(140, 140, 140, 0.14)",
  ring: "rgba(128, 128, 128, 0.7)",

  popover: "#181818",
  popoverForeground: "#F5F5F5",
  foreground: "#F5F5F5",
  mutedForeground: "#808080",
  accentForeground: "#F5F5F5",

  gradientStart: "#3D3D3D",
  gradientEnd: "#E5E5E5",
  gradientHero:
    "radial-gradient(ellipse at top left, #161616 0%, #0A0A0A 38%, #000000 75%)",
  gradientRadial:
    "radial-gradient(circle at top, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 35%, transparent 68%)",

  success: "#5FAE8D",
  successSoft: "rgba(95, 174, 141, 0.08)",
  successBorder: "rgba(95, 174, 141, 0.20)",

  warning: "#C99A4E",
  warningSoft: "rgba(201, 154, 78, 0.08)",
  warningBorder: "rgba(201, 154, 78, 0.20)",

  danger: "#C4787A",
  dangerSoft: "rgba(196, 120, 122, 0.08)",
  dangerBorder: "rgba(196, 120, 122, 0.20)",

  info: "#5FA8B8",
  infoSoft: "rgba(95, 168, 184, 0.08)",
  infoBorder: "rgba(95, 168, 184, 0.20)",
};

export const lightTheme: ThemeTokens = {
  background: "#F2F7F6",
  surface: "#FBFDFC",
  surfaceHover: "#EAF3F1",
  elevated: "#FBFDFC",
  card: "#FBFDFC",
  border: "transparent",
  borderStrong: "transparent",

  textPrimary: "#21403D",
  textSecondary: "#2E524E",
  textMuted: "#6B8B86",
  textInverse: "#F2F7F6",

  accent: "#1A3A36",
  accentSoft: "rgba(0, 0, 0, 0.055)",
  accentSoftBorder: "transparent",

  btnPrimaryFrom: "#3E8F84",
  btnPrimaryTo: "#56A69A",
  btnPrimaryText: "#FBFDFC",
  btnSecondaryBg: "rgba(30, 76, 74, 0.035)",
  btnSecondaryBorder: "transparent",
  btnSecondaryText: "#2E524E",

  inputBg: "#EFF3F2",
  inputBorder: "transparent",
  inputText: "#21403D",
  inputPlaceholder: "rgba(107, 139, 134, 0.45)",

  shadow:
    "0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 10px 0 rgba(0, 0, 0, 0.19)",
  shadowGlow: "0 0 32px -16px rgba(62, 143, 132, 0.20)",
  ring: "rgba(62, 143, 132, 0.26)",

  popover: "#FBFDFC",
  popoverForeground: "#21403D",
  foreground: "#21403D",
  mutedForeground: "#6B8B86",
  accentForeground: "#FBFDFC",

  gradientStart: "#0F1E1C",
  gradientEnd: "#1A3A36",
  gradientHero:
    "linear-gradient(135deg, rgba(26,58,54,0.08) 0%, rgba(251,253,252,0.96) 42%, rgba(26,58,54,0.06) 100%)",
  gradientRadial:
    "radial-gradient(circle at top, rgba(0,0,0,0.04) 0%, rgba(0,0,0,0.02) 40%, transparent 70%)",

  success: "#4C8F72",
  successSoft: "rgba(76, 143, 114, 0.07)",
  successBorder: "rgba(76, 143, 114, 0.18)",

  warning: "#B08036",
  warningSoft: "rgba(176, 128, 54, 0.07)",
  warningBorder: "rgba(176, 128, 54, 0.18)",

  danger: "#B25658",
  dangerSoft: "rgba(178, 86, 88, 0.07)",
  dangerBorder: "rgba(178, 86, 88, 0.18)",

  info: "#4A889A",
  infoSoft: "rgba(74, 136, 154, 0.07)",
  infoBorder: "rgba(74, 136, 154, 0.18)",
};

export const themes: Record<ThemeName, ThemeTokens> = {
  dark: darkTheme,
  light: lightTheme,
};

// Maps each token key to the CSS custom property name written on :root.
export const cssVarMap: Record<keyof ThemeTokens, string> = {
  background: "--background",
  surface: "--surface",
  surfaceHover: "--surface-hover",
  elevated: "--elevated",
  card: "--card",
  border: "--border",
  borderStrong: "--border-strong",
  textPrimary: "--text-primary",
  textSecondary: "--text-secondary",
  textMuted: "--text-muted",
  textInverse: "--text-inverse",
  accent: "--accent",
  accentSoft: "--accent-soft",
  accentSoftBorder: "--accent-soft-border",
  btnPrimaryFrom: "--btn-primary-from",
  btnPrimaryTo: "--btn-primary-to",
  btnPrimaryText: "--btn-primary-text",
  btnSecondaryBg: "--btn-secondary-bg",
  btnSecondaryBorder: "--btn-secondary-border",
  btnSecondaryText: "--btn-secondary-text",
  inputBg: "--input-bg",
  inputBorder: "--input-border",
  inputText: "--input-text",
  inputPlaceholder: "--input-placeholder",
  shadow: "--shadow",
  shadowGlow: "--shadow-glow",
  ring: "--ring",
  popover: "--popover",
  popoverForeground: "--popover-foreground",
  foreground: "--foreground",
  mutedForeground: "--muted-foreground",
  accentForeground: "--accent-foreground",
  gradientStart: "--gradient-start",
  gradientEnd: "--gradient-end",
  gradientHero: "--gradient-hero",
  gradientRadial: "--gradient-radial",
  success: "--success",
  successSoft: "--success-soft",
  successBorder: "--success-border",
  warning: "--warning",
  warningSoft: "--warning-soft",
  warningBorder: "--warning-border",
  danger: "--danger",
  dangerSoft: "--danger-soft",
  dangerBorder: "--danger-border",
  info: "--info",
  infoSoft: "--info-soft",
  infoBorder: "--info-border",
};

export const THEME_STORAGE_KEY = "intereview-theme";
export const THEME_COOKIE_KEY = "intereview-theme";
export const DEFAULT_THEME: ThemeName = "light";
