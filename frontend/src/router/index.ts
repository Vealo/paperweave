import { createRouter, createWebHistory } from "vue-router";

import ProjectDetailView from "../views/ProjectDetailView.vue";
import ProjectsView from "../views/ProjectsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "projects", component: ProjectsView },
    {
      path: "/projects/:projectId",
      name: "project-detail",
      component: ProjectDetailView,
      props: true,
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});
