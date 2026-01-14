import { ref } from "vue";
import { defineStore } from "pinia";

interface UserInfo {
  id: number;
  username: string;
  role: string;
  full_name: string;
}

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const userInfo = ref<UserInfo | null>(null);

  function setToken(newToken: string) {
    token.value = newToken;
    localStorage.setItem("token", newToken);
  }

  function setUserInfo(info: UserInfo) {
    userInfo.value = info;
  }

  function clearToken() {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
  }

  return { token, userInfo, setToken, setUserInfo, clearToken };
});
