// Shared design tokens — single source of truth, derived exactly from DESIGN.md.
// DESIGN.md is authoritative for colors, type, spacing, radius, components.
// Do not invent new colors/fonts; reuse these tokens everywhere.

export const colors = {
  primary: "#cc0000",
  primaryHover: "#aa0000",
  ink: "#1a1a1a",
  inkMid: "#333333",
  inkMuted: "#666666",
  canvas: "#f5f5f5",
  canvasDark: "#0d0d0d",
  surface1: "#1e1e1e",
  hairline: "#e0e0e0",
  hairlineDark: "#2e2e2e",
  inkWhite: "#ffffff",
  inkWhiteMuted: "#b3b3b3",
  shadow: "#000000",
};

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
  xxl: "48px",
  xxxl: "64px",
  xxxxl: "96px",
};

export const rounded = {
  none: "0px",
  sm: "2px",
  md: "4px",
  pill: "100px",
  full: "9999px",
};

// Font stacks per DESIGN.md. Acura Precision Display / Acura Text are
// proprietary; Rajdhani (display) + Inter (body) are the documented substitutes.
export const fonts = {
  display: '"Rajdhani", "Acura Precision Display", Arial, sans-serif',
  body: '"Inter", "Acura Text", Arial, sans-serif',
};

export const typography = {
  displayXl: {
    fontFamily: fonts.display,
    fontSize: "64px",
    fontWeight: 700,
    lineHeight: "68px",
    letterSpacing: "-0.5px",
  },
  displayLg: {
    fontFamily: fonts.display,
    fontSize: "48px",
    fontWeight: 700,
    lineHeight: "52px",
    letterSpacing: "-0.5px",
  },
  displayMd: {
    fontFamily: fonts.display,
    fontSize: "32px",
    fontWeight: 400,
    lineHeight: "38px",
    letterSpacing: "0",
  },
  headingMd: {
    fontFamily: fonts.display,
    fontSize: "24px",
    fontWeight: 400,
    lineHeight: "30px",
    letterSpacing: "0",
  },
  bodyLg: { fontFamily: fonts.body, fontSize: "18px", fontWeight: 400, lineHeight: "28px" },
  bodyMd: { fontFamily: fonts.body, fontSize: "16px", fontWeight: 400, lineHeight: "24px" },
  bodySm: { fontFamily: fonts.body, fontSize: "14px", fontWeight: 400, lineHeight: "20px" },
  labelMd: {
    fontFamily: fonts.body,
    fontSize: "14px",
    fontWeight: 500,
    lineHeight: "20px",
    letterSpacing: "0.5px",
  },
  caption: { fontFamily: fonts.body, fontSize: "12px", fontWeight: 400, lineHeight: "16px" },
  buttonMd: {
    fontFamily: fonts.body,
    fontSize: "16px",
    fontWeight: 500,
    lineHeight: "16px",
    letterSpacing: "1px",
  },
  navLink: { fontFamily: fonts.body, fontSize: "14px", fontWeight: 400, lineHeight: "20px" },
};

export const ROLES = {
  SUPER_ADMIN: "SUPER_ADMIN",
  ADMIN: "ADMIN",
  SUPER_VIEWER: "SUPER_VIEWER",
  TENANT_ADMIN: "TENANT_ADMIN",
  TENANT_USER: "TENANT_USER",
};
