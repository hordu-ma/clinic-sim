import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import CaseList from "../views/CaseList.vue";
import Chat from "../views/Chat.vue";
import SessionList from "../views/SessionList.vue";
import { useUserStore } from "../stores/user";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      redirect: "/cases",
    },
    {
      path: "/login",
      name: "login",
      component: Login,
    },
    {
      path: "/cases",
      name: "cases",
      component: CaseList,
      meta: { requiresAuth: true },
    },
    {
      path: "/chat/:sessionId",
      name: "chat",
      component: Chat,
      meta: { requiresAuth: true },
    },
    {
      path: "/sessions",
      name: "sessions",
      component: SessionList,
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore();
  if (to.meta.requiresAuth && !userStore.token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
