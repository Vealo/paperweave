import { createRouter, createWebHistory } from "vue-router";

import { getAuthStatus, getCurrentUser, isSessionError } from "../api/auth";
import AccessDeniedView from "../views/AccessDeniedView.vue";
import LoginView from "../views/LoginView.vue";
import ProjectDetailView from "../views/ProjectDetailView.vue";
import ProfileView from "../views/ProfileView.vue";
import ProjectsView from "../views/ProjectsView.vue";
import UserManagementView from "../views/UserManagementView.vue";
import UsersView from "../views/UsersView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView },
    { path: "/access-denied", name: "access-denied", component: AccessDeniedView },
    { path: "/", name: "projects", component: ProjectsView, meta: { requiresAuth: true } },
    {
      path: "/projects/:projectId",
      name: "project-detail",
      component: ProjectDetailView,
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: "/profile",
      name: "profile",
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: "/users",
      name: "users",
      component: UserManagementView,
      meta: { requiresAuth: true, ownerOnly: true },
    },
    {
      path: "/users/new",
      name: "users-new",
      component: UsersView,
      meta: { requiresAuth: true, ownerOnly: true },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

router.beforeEach(async (to) => {
  if (to.name === "login" || to.name === "access-denied") return true;
  try {
    const status = await getAuthStatus();
    if (!status.owner_exists) return { name: "login", query: { setup: "1" } };
    const user = await getCurrentUser();
    if (to.meta.ownerOnly && user.role !== "owner") return { name: "access-denied" };
    return true;
  } catch (error) {
    if (isSessionError(error)) return { name: "login", query: { expired: "1" } };
    return { name: "login", query: { unavailable: "1" } };
  }
});
