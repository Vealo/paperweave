import { createApp } from "vue";
import PrimeVue from "primevue/config";

import App from "./App.vue";
import { router } from "./router";
import PaperWeavePreset from "./theme/paperweavePreset";
import "./styles/main.css";

const app = createApp(App);

app.use(PrimeVue, {
  theme: {
    preset: PaperWeavePreset,
    options: {
      darkModeSelector: ".p-dark",
    },
  },
});
app.use(router);
app.mount("#app");
