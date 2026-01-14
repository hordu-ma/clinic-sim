import axios from "axios";
import { showToast } from "vant";
import { useUserStore } from "../stores/user";
import router from "../router";

const service = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore();
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

service.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore();
      userStore.clearToken();
      router.push("/login");
    }
    const errorMsg = error.response?.data?.detail || "请求失败";
    showToast(errorMsg);
    return Promise.reject(error);
  }
);

export default service;
