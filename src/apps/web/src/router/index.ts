import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import CaseList from "../views/CaseList.vue";
import Chat from "../views/Chat.vue";
import SessionList from "../views/SessionList.vue";
import { useUserStore } from "../stores/user";
import { getUserInfo } from "../api/auth";

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

router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore();

  if (!to.meta.requiresAuth) {
    next();
    return;
  }

  if (!userStore.token) {
    next("/login");
    return;
  }

  if (!userStore.userInfo) {
    try {
      const info = await getUserInfo();
      userStore.setUserInfo(info as any);
    } catch (_error) {
      userStore.clearToken();
      next("/login");
      return;
    }
  }

  next();
});

export default router;
