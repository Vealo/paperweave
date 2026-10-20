import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const mainSource = await readFile(new URL("../src/main.ts", import.meta.url), "utf8");
const stylesSource = await readFile(new URL("../src/styles/main.css", import.meta.url), "utf8");
const presetSource = await readFile(new URL("../src/theme/paperweavePreset.ts", import.meta.url), "utf8");

test("PrimeVue dialog masks stretch to the viewport through the shared Pass Through config", () => {
  assert.match(
    mainSource,
    /dialog:\s*\{\s*mask:\s*\{\s*style:\s*\{\s*alignItems:\s*"stretch",\s*justifyContent:\s*"stretch",\s*padding:\s*0/s,
  );
  assert.match(stylesSource, /\.pw-modal-fullscreen\.p-dialog\s*\{[^}]*width:\s*100vw;[^}]*height:\s*100dvh/s);
});

test("logout text uses the dark semantic danger shade on light surfaces", () => {
  assert.match(
    stylesSource,
    /\.account-menu__logout \.p-menu-item-content\s*\{\s*color:\s*var\(--p-red-700\);\s*\}/,
  );
  assert.doesNotMatch(stylesSource, /\.account-menu__logout \.p-menu-item-content\s*\{\s*color:\s*var\(--p-red-500\)/);
});

test("message variants use dark, readable semantic text colors on light surfaces", () => {
  for (const token of ["info", "success", "warning", "danger"]) {
    assert.match(stylesSource, new RegExp(`--pw-color-${token}: #[0-9a-f]{6};`, "i"));
  }
  for (const [severity, token] of [["info", "info"], ["success", "success"], ["warn", "warning"], ["error", "danger"]]) {
    const color = `var\\(--pw-color-${token}\\)`;
    assert.match(
      presetSource,
      new RegExp(`${severity}:\\s*\\{\\s*color: "${color}",\\s*outlined: \\{ color: "${color}" \\},\\s*simple: \\{ color: "${color}" \\}`),
    );
  }
});
