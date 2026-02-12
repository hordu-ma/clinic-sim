import { ref } from "vue";
import { defineStore } from "pinia";

interface UserInfo {
  id: number;
  username: string;
  role: string;
  full_name: string;
}

const USER_INFO_STORAGE_KEY = "userInfo";

function loadUserInfoFromStorage(): UserInfo | null {
  const raw = localStorage.getItem(USER_INFO_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    localStorage.removeItem(USER_INFO_STORAGE_KEY);
    return null;
  }
}

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const userInfo = ref<UserInfo | null>(loadUserInfoFromStorage());

  function setToken(newToken: string) {
    token.value = newToken;
    localStorage.setItem("token", newToken);
  }

  function setUserInfo(info: UserInfo) {
    userInfo.value = info;
    localStorage.setItem(USER_INFO_STORAGE_KEY, JSON.stringify(info));
  }

  function clearToken() {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem(USER_INFO_STORAGE_KEY);
  }

  return { token, userInfo, setToken, setUserInfo, clearToken };
});
