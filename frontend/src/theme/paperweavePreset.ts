import Aura from "@primeuix/themes/aura";
import { definePreset } from "@primeuix/themes";

/** Apply the project-owned CSS palette through Aura's public semantic token API. */
const PaperWeavePreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: "var(--pw-surface-selected)",
      100: "var(--pw-surface-selected-hover)",
      200: "var(--pw-surface-selected-hover)",
      300: "var(--pw-color-marker)",
      400: "var(--pw-color-link)",
      500: "var(--pw-color-primary)",
      600: "var(--pw-color-primary)",
      700: "var(--pw-color-primary-strong)",
      800: "var(--pw-color-primary-strong)",
      900: "var(--pw-color-primary-strong)",
      950: "var(--pw-color-primary-strong)",
      color: "var(--pw-color-primary)",
      contrastColor: "#ffffff",
      hoverColor: "var(--pw-color-primary-strong)",
      activeColor: "var(--pw-color-primary-strong)",
    },
    focusRing: {
      color: "var(--pw-color-focus)",
    },
    formField: {
      focusRing: {
        width: "2px",
        style: "solid",
        color: "var(--pw-color-focus)",
        offset: "1px",
        shadow: "none",
      },
    },
    highlight: {
      background: "var(--pw-surface-selected)",
      focusBackground: "var(--pw-surface-selected-hover)",
      color: "var(--pw-color-primary-strong)",
      focusColor: "var(--pw-color-primary-strong)",
    },
  },
});

export default PaperWeavePreset;
