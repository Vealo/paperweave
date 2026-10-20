import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const appSource = await readFile(new URL("../src/App.vue", import.meta.url), "utf8");
const mainSource = await readFile(new URL("../src/main.ts", import.meta.url), "utf8");
const profileSource = await readFile(new URL("../src/views/ProfileView.vue", import.meta.url), "utf8");
const authSource = await readFile(new URL("../src/api/auth.ts", import.meta.url), "utf8");

test("application bootstrap clears stale dark mode before rendering", () => {
  assert.match(mainSource, /document\.documentElement\.classList\.remove\("p-dark"\)/);
  assert.ok(mainSource.indexOf('classList.remove("p-dark")') < mainSource.indexOf("app.mount(\"#app\")"));
});

test("app shell does not independently load or apply user or OS theme settings", () => {
  assert.doesNotMatch(appSource, /getUserSettings|applyTheme|matchMedia|p-dark/);
});

test("profile page does not expose or persist an inactive theme preference", () => {
  assert.doesNotMatch(profileSource, /getUserSettings|updateUserSettings|profile-theme|themeOptions|applyTheme|matchMedia|p-dark/);
  assert.match(authSource, /theme: "light"/);
});
