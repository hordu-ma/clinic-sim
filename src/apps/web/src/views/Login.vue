<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { showToast } from "vant";
import { useUserStore } from "../stores/user";
import { login, getUserInfo } from "../api/auth";

const router = useRouter();
const userStore = useUserStore();

const username = ref("");
const password = ref("");
const loading = ref(false);

const onSubmit = async () => {
  if (!username.value || !password.value) {
    showToast("请输入用户名和密码");
    return;
  }

  loading.value = true;
  try {
    const res: any = await login({
      username: username.value,
      password: password.value,
    });

    // 假设 res 就是 Token 对象，或者 res.access_token 存在
    // 这里需要根据 request.ts 的响应拦截器调整
    // request.ts 返回 response.data
    // 如果 login 接口只返回 token
    userStore.setToken(res.access_token);

    // 获取用户信息
    const userRes: any = await getUserInfo();
    userStore.setUserInfo(userRes);

    showToast("登录成功");
    router.push("/");
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="login-page">
    <div class="header">
      <h2>Clinic Sim</h2>
      <p>临床医学模拟问诊系统</p>
    </div>

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请填写用户名' }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>
      <div style="margin: 30px 16px">
        <van-button
          round
          block
          type="primary"
          native-type="submit"
          :loading="loading"
        >
          登录
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background-color: #f7f8fa;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h2 {
  margin-bottom: 10px;
  color: #323233;
}

.header p {
  color: #969799;
  font-size: 14px;
}
</style>
